"""
간단한 WebSocket 연결 테스트
"""
import asyncio
import json
import sys
from websockets.client import connect

WS_URL = "ws://localhost:8000/api/chat/ws"

async def test():
    print("=" * 60)
    print("WebSocket 연결 테스트")
    print("=" * 60)
    print(f"연결 URL: {WS_URL}\n")
    
    try:
        print("연결 시도 중...")
        async with connect(WS_URL) as websocket:
            print("✓ 연결 성공!\n")
            
            # 테스트 메시지 전송
            request = {
                "type": "message",
                "session_id": "test-session-001",
                "turn_id": 1,
                "message": "안녕하세요",
                "exam_id": 1,
                "participant_id": 100,
                "spec_id": 10,
            }
            
            print("메시지 전송 중...")
            await websocket.send(json.dumps(request))
            print("✓ 메시지 전송 완료\n")
            print("응답 대기 중...\n")
            print("받은 메시지:")
            print("-" * 60)
            
            # 첫 번째 응답만 받기
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print("-" * 60)
                print("\n✓ 테스트 성공!")
            except asyncio.TimeoutError:
                print("✗ 타임아웃: 10초 내에 응답을 받지 못했습니다")
                sys.exit(1)
    
    except ConnectionRefusedError:
        print("✗ 연결 실패: 서버가 실행 중이 아닙니다")
        print("  서버를 먼저 실행하세요: uv run scripts/run_dev.py")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test())

