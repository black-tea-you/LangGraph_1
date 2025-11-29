# 백엔드 통신 기능 현황

## 📋 요구사항 vs 구현 상태

### 1. 챗봇 WS 토큰 스트리밍 ❌ **미구현**

**요구사항:**
- `wss:/chat` 양방향 WebSocket
- Delta 스트리밍 (토큰 단위)
- 취소 기능
- turnId 전달
- FastAPI WS 핸들러

**현재 상태:**
- ❌ WebSocket 핸들러 없음
- ✅ REST API만 존재: `POST /api/chat/message`
- ❌ 스트리밍 없음 (전체 응답만 반환)

**현재 구현:**
```python
# app/presentation/api/routes/chat.py
@router.post("/message")
async def send_message(...) -> ChatResponse:
    # 전체 응답을 한 번에 반환
    result = await eval_service.process_message(...)
    return ChatResponse(ai_message=result.get("ai_message"))
```

**필요한 구현:**
```python
# WebSocket 엔드포인트 추가 필요
@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    # Delta 스트리밍
    # 취소 기능
    # turnId 전달
```

---

### 2. Usage 콜백 ❌ **미구현**

**요구사항:**
- 프롬프트/컴플리션/합계 사용량 Core로 리턴
- callback, retry

**현재 상태:**
- ❌ Usage 콜백 메서드 없음
- ✅ CallbackService는 있지만 usage 관련 없음
- ✅ Retry 로직 없음

**현재 구현:**
```python
# app/application/services/callback_service.py
class CallbackService:
    async def send_message_response(...)  # ✅ 있음
    async def send_turn_evaluation(...)  # ✅ 있음
    async def send_final_scores(...)      # ✅ 있음
    async def send_error(...)             # ✅ 있음
    # ❌ send_usage() 없음
```

**필요한 구현:**
```python
async def send_usage(
    self,
    session_id: str,
    turn: int,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> bool:
    """Usage 콜백 전송"""
    payload = {
        "type": "usage",
        "session_id": session_id,
        "turn": turn,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
    return await self._send_callback(payload, retry=True)
```

**호출 위치:**
- `app/domain/langgraph/nodes/writer.py`: LLM 응답 후 usage 추출
- `app/application/services/eval_service.py`: Usage 콜백 호출

---

### 3. 대화 저장 ⚠️ **부분 구현**

**요구사항:**
- `prompt_sessions` / `prompt_messages` 저장
- repo, schema DTO

**현재 상태:**
- ✅ Repository 구현 완료 (`SessionRepository`)
- ✅ Model 정의 완료 (`PromptSession`, `PromptMessage`)
- ✅ Schema DTO 있음
- ❌ **실제 호출 안 됨** (`eval_service.py`에서 호출 없음)

**현재 구현:**
```python
# app/infrastructure/repositories/session_repository.py
class SessionRepository:
    async def create_session(...)      # ✅ 구현됨
    async def add_message(...)         # ✅ 구현됨
    async def save_messages_batch(...) # ✅ 구현됨
    async def end_session(...)         # ✅ 구현됨
```

**문제점:**
```python
# app/application/services/eval_service.py
# ❌ SessionRepository를 사용하지 않음
# ❌ create_session() 호출 없음
# ❌ add_message() 호출 없음
```

**필요한 구현:**
```python
# eval_service.py에 추가 필요
async def process_message(...):
    # 1. 세션 조회/생성
    session = await session_repo.get_active_session(...)
    if not session:
        session = await session_repo.create_session(...)
    
    # 2. LangGraph 실행
    result = await self.graph.ainvoke(...)
    
    # 3. 메시지 저장
    await session_repo.add_message(
        session_id=session.id,
        turn=result.get("turn"),
        role=PromptRoleEnum.USER,
        content=human_message
    )
    await session_repo.add_message(
        session_id=session.id,
        turn=result.get("turn"),
        role=PromptRoleEnum.ASSISTANT,
        content=result.get("ai_message")
    )
```

---

## 📊 구현 상태 요약

| 기능 | 상태 | 구현도 | 우선순위 |
|-----|------|--------|---------|
| **WebSocket 스트리밍** | ❌ 미구현 | 0% | 높음 |
| **Usage 콜백** | ❌ 미구현 | 0% | 중간 |
| **대화 저장** | ⚠️ 부분 구현 | 50% | 높음 |

---

## 🔧 구현 필요 사항

### 1. WebSocket 스트리밍 (높은 우선순위)

**파일:** `app/presentation/api/routes/chat.py`

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_json()
            session_id = data.get("session_id")
            message = data.get("message")
            turn_id = data.get("turn_id")
            
            # Delta 스트리밍
            async for chunk in eval_service.process_message_stream(...):
                await websocket.send_json({
                    "type": "delta",
                    "content": chunk,
                    "turn_id": turn_id
                })
                
            # 완료 신호
            await websocket.send_json({
                "type": "done",
                "turn_id": turn_id
            })
    except WebSocketDisconnect:
        pass
```

### 2. Usage 콜백 (중간 우선순위)

**파일:** `app/application/services/callback_service.py`

```python
async def send_usage(
    self,
    session_id: str,
    turn: int,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> bool:
    """Usage 콜백 전송 (재시도 포함)"""
    payload = {
        "type": "usage",
        "session_id": session_id,
        "turn": turn,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
    
    # 재시도 로직
    max_retries = 3
    for attempt in range(max_retries):
        success = await self._send_callback(payload)
        if success:
            return True
        await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return False
```

**호출 위치:** `app/domain/langgraph/nodes/writer.py`

```python
# LLM 응답 후 usage 추출
response = await llm.ainvoke(...)
usage = response.response_metadata.get("usage", {})

# Usage 콜백 전송
await callback_service.send_usage(
    session_id=state.get("session_id"),
    turn=state.get("current_turn"),
    prompt_tokens=usage.get("prompt_tokens", 0),
    completion_tokens=usage.get("completion_tokens", 0),
    total_tokens=usage.get("total_tokens", 0),
)
```

### 3. 대화 저장 연동 (높은 우선순위)

**파일:** `app/application/services/eval_service.py`

```python
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.persistence.models.enums import PromptRoleEnum
from app.infrastructure.persistence.session import get_db_context

class EvalService:
    def __init__(self, redis: RedisClient):
        self.redis = redis
        self.state_repo = StateRepository(redis)
        # ✅ SessionRepository 추가 필요
        # self.session_repo = SessionRepository(get_db_context())
    
    async def process_message(...):
        # 1. 세션 조회/생성
        async with get_db_context() as db:
            session_repo = SessionRepository(db)
            session = await session_repo.get_active_session(
                exam_id, participant_id
            )
            if not session:
                session = await session_repo.create_session(
                    exam_id, participant_id, spec_id
                )
        
        # 2. LangGraph 실행
        result = await self.graph.ainvoke(...)
        
        # 3. 메시지 저장
        async with get_db_context() as db:
            session_repo = SessionRepository(db)
            await session_repo.add_message(
                session_id=session.id,
                turn=result.get("turn"),
                role=PromptRoleEnum.USER,
                content=human_message
            )
            await session_repo.add_message(
                session_id=session.id,
                turn=result.get("turn"),
                role=PromptRoleEnum.ASSISTANT,
                content=result.get("ai_message")
            )
```

---

## ✅ 결론

**현재 상태:**
- ❌ WebSocket 스트리밍: 미구현
- ❌ Usage 콜백: 미구현
- ⚠️ 대화 저장: Repository는 있지만 연동 안 됨

**다음 단계:**
1. 대화 저장 연동 (가장 중요, Repository는 이미 있음)
2. WebSocket 스트리밍 구현
3. Usage 콜백 구현

