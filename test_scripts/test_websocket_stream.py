"""
WebSocket 스트리밍 테스트 스크립트

[목적]
- WebSocket 엔드포인트의 스트리밍 기능 테스트
- LangGraph를 통한 실시간 토큰 스트리밍 확인
- Delta 메시지 수신 확인

[사용법]
python test_scripts/test_websocket_stream.py
"""
import asyncio
import json
import logging
from websockets.client import connect
from websockets.exceptions import ConnectionClosed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 테스트 설정
WS_URL = "ws://localhost:8000/api/chat/ws"
SESSION_ID = "test-websocket-session-001"
EXAM_ID = 1
PARTICIPANT_ID = 100
SPEC_ID = 10

TEST_MESSAGES = [
    "파이썬으로 리스트를 정렬하는 방법을 알려줘",
    "그럼 내림차순으로 정렬하려면?",
]


async def test_websocket_stream():
    """WebSocket 스트리밍 테스트"""
    try:
        print(f"\n{'='*60}")
        print(f"WebSocket 테스트 시작")
        print(f"연결 URL: {WS_URL}")
        print(f"{'='*60}\n")
        logger.info(f"WebSocket 연결 시도: {WS_URL}")
        
        async with connect(WS_URL) as websocket:
            logger.info("WebSocket 연결 성공")
            
            for turn_id, message in enumerate(TEST_MESSAGES, start=1):
                logger.info(f"\n{'='*60}")
                logger.info(f"턴 {turn_id} 시작: {message}")
                logger.info(f"{'='*60}")
                
                # 메시지 전송
                request = {
                    "type": "message",
                    "session_id": SESSION_ID,
                    "turn_id": turn_id,
                    "message": message,
                    "exam_id": EXAM_ID,
                    "participant_id": PARTICIPANT_ID,
                    "spec_id": SPEC_ID,
                }
                
                await websocket.send(json.dumps(request))
                print(f"[턴 {turn_id}] 메시지 전송: {message[:50]}...")
                logger.info(f"메시지 전송 완료: {message[:50]}...")
                
                # 응답 수신
                full_content = ""
                delta_count = 0
                
                while True:
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=60.0  # 60초 타임아웃
                        )
                        
                        data = json.loads(response)
                        msg_type = data.get("type")
                        
                        if msg_type == "delta":
                            # Delta 스트리밍
                            chunk = data.get("content", "")
                            full_content += chunk
                            delta_count += 1
                            
                            # 첫 번째 토큰과 마지막 토큰만 로깅 (너무 많으면 로그가 길어짐)
                            if delta_count == 1:
                                logger.info(f"[Delta #{delta_count}] 첫 토큰: '{chunk}'")
                            elif delta_count % 10 == 0:
                                logger.info(f"[Delta #{delta_count}] 진행 중... (현재 길이: {len(full_content)} 문자)")
                            
                            # 실시간 출력 (선택적)
                            print(chunk, end="", flush=True)
                        
                        elif msg_type == "done":
                            # 완료 신호
                            logger.info(f"\n[완료] 총 {delta_count}개의 delta 메시지 수신")
                            logger.info(f"전체 응답 길이: {len(full_content)} 문자")
                            logger.info(f"전체 응답 (처음 200자): {full_content[:200]}...")
                            break
                        
                        elif msg_type == "error":
                            # 에러 발생
                            error_msg = data.get("error", "알 수 없는 오류")
                            print(f"\n✗ [에러] {error_msg}")
                            logger.error(f"[에러] {error_msg}")
                            break
                        
                        elif msg_type == "cancelled":
                            # 취소됨
                            logger.warning("[취소] 스트리밍이 취소되었습니다")
                            break
                        
                        else:
                            logger.warning(f"[알 수 없는 메시지 타입] {msg_type}: {data}")
                    
                    except asyncio.TimeoutError:
                        print("\n✗ [타임아웃] 60초 내에 응답을 받지 못했습니다")
                        logger.error("[타임아웃] 60초 내에 응답을 받지 못했습니다")
                        break
                
                # 턴 간 대기
                if turn_id < len(TEST_MESSAGES):
                    logger.info("\n다음 턴을 위해 2초 대기...")
                    await asyncio.sleep(2)
            
            logger.info(f"\n{'='*60}")
            logger.info("모든 테스트 완료")
            logger.info(f"{'='*60}")
    
    except ConnectionClosed:
        print("\n✗ WebSocket 연결이 종료되었습니다")
        logger.error("WebSocket 연결이 종료되었습니다")
    
    except Exception as e:
        print(f"\n✗ 테스트 중 오류 발생: {str(e)}")
        logger.error(f"테스트 중 오류 발생: {str(e)}", exc_info=True)


async def test_cancel_functionality():
    """취소 기능 테스트"""
    try:
        logger.info(f"\n{'='*60}")
        logger.info("취소 기능 테스트 시작")
        logger.info(f"{'='*60}")
        
        async with connect(WS_URL) as websocket:
            logger.info("WebSocket 연결 성공")
            
            # 메시지 전송
            request = {
                "type": "message",
                "session_id": f"{SESSION_ID}-cancel",
                "turn_id": 1,
                "message": "긴 답변을 생성해주세요. 최대한 길게 설명해주세요.",
                "exam_id": EXAM_ID,
                "participant_id": PARTICIPANT_ID,
                "spec_id": SPEC_ID,
            }
            
            await websocket.send(json.dumps(request))
            logger.info("메시지 전송 완료")
            
            # 몇 개의 delta를 받은 후 취소
            delta_count = 0
            cancel_after = 5
            
            while True:
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=10.0
                    )
                    
                    data = json.loads(response)
                    msg_type = data.get("type")
                    
                    if msg_type == "delta":
                        delta_count += 1
                        chunk = data.get("content", "")
                        print(chunk, end="", flush=True)
                        
                        if delta_count >= cancel_after:
                            logger.info(f"\n[{delta_count}개 delta 수신 후 취소 요청]")
                            # 취소 요청 전송
                            cancel_request = {
                                "type": "cancel",
                                "turn_id": 1
                            }
                            await websocket.send(json.dumps(cancel_request))
                            logger.info("취소 요청 전송 완료")
                    
                    elif msg_type == "cancelled":
                        logger.info("\n[취소 확인] 스트리밍이 취소되었습니다")
                        break
                    
                    elif msg_type == "done":
                        logger.warning("\n[완료] 취소 요청이 제대로 작동하지 않았습니다")
                        break
                    
                    elif msg_type == "error":
                        error_msg = data.get("error", "알 수 없는 오류")
                        logger.error(f"[에러] {error_msg}")
                        break
                
                except asyncio.TimeoutError:
                    logger.warning("[타임아웃] 10초 내에 응답을 받지 못했습니다")
                    break
                
    except Exception as e:
        logger.error(f"취소 테스트 중 오류 발생: {str(e)}", exc_info=True)
        


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cancel":
        # 취소 기능 테스트
        asyncio.run(test_cancel_functionality())
    else:
        # 기본 스트리밍 테스트
        asyncio.run(test_websocket_stream())


