import requests
import json
import time
import asyncio

user_id = "lucas-123"
def query_with_sse(query: str):
    """SSE 방식으로 쿼리 전송 및 결과 수신"""
    url = f"http://localhost:8000/api/mcp/query-sse"
    params = {'query': query, 'user_id': user_id}
    # stream=True로 SSE 수신
    with requests.get(url, params=params, stream=True) as response:
        print(f"연결됨 (상태 코드: {response.status_code})")
        
        for line in response.iter_lines():
            if line:
                # SSE 형식: "data: {...}"
                line_str = line.decode('utf-8')
                
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # "data: " 제거
                    data = json.loads(data_str)
                    
                    print(f"\n[이벤트 받음]")
                    if data['status'] == 'processing':
                        #print(f"처리 중: {data['query']}")
                        print(f"처리 중: {data['result']}")
                    elif data['status'] == 'completed':
                        print(f"완료: {data['result']}")
                    elif data['status'] == 'error':
                        print(f"에러: {data['result']}")
                        break

# 사용 예시
if __name__ == "__main__":
    query_with_sse("100과 20을 더한 다음, 그 결과에 4를 곱해주세요")
    time.sleep(1)  # 잠시 대기
    query_with_sse("결과값에서 30을 뺀 값을 알려줘")
    # time.sleep(1)  # 잠시 대기
    # query_with_sse("대한민국의 수도는 어디인가요?")
    # time.sleep(1)  # 잠시 대기
    # query_with_sse("그 수도의 인구는 몇 명인가요?")