import asyncio
import websockets
import aiohttp
import json

on_running = True

async def websocket_client(client_id: str):
    """WebSocket 연결 및 메시지 수신"""
    uri = f"ws://localhost:8000/ws/{client_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"WebSocket 연결됨: {client_id}")
        global on_running
        while on_running:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                print(f"\n[알림 받음]")
                if data['status'] == 'processing':
                    print(f"결과: {data['result']}")
                elif data['status'] == 'completed':
                    print(f"결과: {data['result']}")
                    on_running = False
                elif data['status'] == 'error':
                    print(f"에러: {data['error']}")
                    
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket 연결 종료")
                break
        

async def send_query(query: str, client_id: str):
    """HTTP POST로 쿼리 전송"""
    async with aiohttp.ClientSession() as session:
        params = {
            'query': query,
            'client_id': client_id
        }
        
        async with session.post('http://localhost:8000/api/mcp/query-websocket2', params=params) as response:
            result = await response.json()
            print(f"쿼리 제출됨: {result}")

async def main():
    client_id = "python-client-123"
    
    # WebSocket 연결 시작 (백그라운드)
    ws_task = asyncio.create_task(websocket_client(client_id))
    
    # 잠시 대기 (WebSocket 연결 완료)
    await asyncio.sleep(1)
    
    # 쿼리 전송
    await send_query("100과 50을 더한 다음, 그 결과에 2를 곱해주세요", client_id)
    
    # WebSocket 메시지 대기
    global on_running
    while on_running:
        await asyncio.sleep(1)
    
    ws_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())