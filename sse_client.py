import requests
import json

def query_with_sse(query: str):
    """SSE 방식으로 쿼리 전송 및 결과 수신"""
    url = f"http://localhost:8000/api/mcp/query-sse"
    params = {'query': query}
    
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
                        break

# 사용 예시
if __name__ == "__main__":
    query_with_sse("100과 50을 더한 다음, 그 결과에 2를 곱해주세요")