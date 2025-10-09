"""
Math Operations MCP Server using Claude Agent SDK
add와 multiply 기능을 제공하는 SDK MCP 서버
"""

import anyio
import json
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import SystemMessage, AssistantMessage, UserMessage, ResultMessage

# Add 도구 정의
@tool(
    name="add",
    description="두 숫자를 더합니다",
    input_schema={
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
                "description": "첫 번째 숫자"
            },
            "b": {
                "type": "number",
                "description": "두 번째 숫자"
            }
        },
        "required": ["a", "b"]
    }
)
async def add(args):
    """두 숫자를 더하는 함수"""
    a = args.get("a")
    b = args.get("b")
    
    if a is None or b is None:
        return {
            "content": [
                {"type": "text", "text": "오류: a와 b 파라미터가 필요합니다"}
            ],
            "isError": True
        }
    
    result = a + b
    return {
        "content": [
            {"type": "text", "text": f"{a} + {b} = {result}"}
        ]
    }


# Multiply 도구 정의
@tool(
    name="multiply",
    description="두 숫자를 곱합니다",
    input_schema={
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
                "description": "첫 번째 숫자"
            },
            "b": {
                "type": "number",
                "description": "두 번째 숫자"
            }
        },
        "required": ["a", "b"]
    }
)
async def multiply(args):
    """두 숫자를 곱하는 함수"""
    a = args.get("a")
    b = args.get("b")
    
    if a is None or b is None:
        return {
            "content": [
                {"type": "text", "text": "오류: a와 b 파라미터가 필요합니다"}
            ],
            "isError": True
        }
    
    result = a * b
    return {
        "content": [
            {"type": "text", "text": f"{a} × {b} = {result}"}
        ]
    }


# SDK MCP 서버 생성
math_server = create_sdk_mcp_server(
    name="math-operations",
    version="1.0.0",
    tools=[add, multiply]
)

# Claude Agent 옵션 설정
options = ClaudeAgentOptions(
    mcp_servers={"math": math_server},
    allowed_tools=["mcp__math__add", "mcp__math__multiply"],
    system_prompt="당신은 수학 연산을 도와주는 AI 어시스턴트입니다. add와 multiply 도구를 사용하여 계산을 수행하세요."
)
print("=== Math Operations MCP Server ===\n")

async def ai_query(message: str):
    """
    Math MCP 서버를 Claude Agent와 함께 실행하는 예제
    """
    result=[]
    # Claude SDK 클라이언트 생성 및 쿼리 실행
    async with ClaudeSDKClient(options=options) as client:
        await client.query(message)
        
        async for msg in client.receive_response():
            print(f"응답: {msg}\n")
            result.append(f"응답: {msg}\n")
        
        print("=" * 50 + "\n")
        return result
    
async def ai_stream_generator(query: str):
    """
    Server-Sent Events (SSE) 방식으로 AI 쿼리를 처리하고 결과를 스트리밍
    """
    # Claude SDK 클라이언트 생성 및 쿼리 실행
    async with ClaudeSDKClient(options=options) as client:
        await client.query(query)
        
        async for msg in client.receive_response():
            print(f"응답: {msg}\n")
            """AI 처리 결과를 스트리밍"""
            if isinstance(msg, ResultMessage):
                yield f"data: {json.dumps({'status': 'completed', 'result': str(msg.result)})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'processing', 'result': str(msg)})}\n\n"
        print("=" * 50 + "\n")

async def ai_websocket_generator(query: str, client_id: str, active_connections):
    """
    백그라운드 태스크 + WebSocket 방식으로 AI 쿼리를 처리하고 결과를 전송
    """
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(query)
            
            async for msg in client.receive_response():
                print(f"응답: {msg}\n")
                # WebSocket으로 결과 전송
                """AI 처리 결과를 스트리밍"""
                if client_id in active_connections:
                    data = {}
                    if isinstance(msg, ResultMessage):
                        data = {
                            "status": "completed",
                            "result": f"응답: {str(msg.result)}\n\n"
                        }
                    else:
                        data = {
                            "status": "processing",
                            "result": f"응답: {str(msg)}\n\n"
                        }
                    await active_connections[client_id].send_json(data)
            print("=" * 50 + "\n")
    except Exception as e:
        if client_id in active_connections:
            await active_connections[client_id].send_json({
                "status": "error",
                "error": str(e)
            })
            
async def main():
    """
    Math MCP 서버를 Claude Agent와 함께 실행하는 예제
    """
    # Claude SDK 클라이언트 생성 및 쿼리 실행
    async with ClaudeSDKClient(options=options) as client:
        # 테스트 1: 덧셈
        print("테스트 1: 25 + 17 계산")
        await client.query("25와 17을 더해주세요")
        async for msg in client.receive_response():
            print(f"응답: {msg}\n")
        
        print("=" * 50 + "\n")
        
        # 테스트 2: 곱셈
        print("테스트 2: 12 x 8 계산")
        await client.query("12와 8을 곱해주세요")
        async for msg in client.receive_response():
            print(f"응답: {msg}\n")
        
        print("=" * 50 + "\n")
        
        # 테스트 3: 복합 연산
        print("테스트 3: 복합 연산")
        await client.query("100과 50을 더한 다음, 그 결과에 2를 곱해주세요")
        async for msg in client.receive_response():
            print(f"응답: {msg}\n")


async def standalone_usage():
    """
    다른 프로젝트에서 이 MCP 서버를 사용하는 예제
    """
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
    
    # math_server를 다른 서버들과 함께 사용
    options = ClaudeAgentOptions(
        mcp_servers={
            "math": math_server,
            # 다른 외부 MCP 서버도 함께 사용 가능
            # "external": {
            #     "type": "stdio",
            #     "command": "python",
            #     "args": ["-m", "other_server"]
            # }
        },
        allowed_tools=["mcp__math__add", "mcp__math__multiply"]
    )
    
    async with ClaudeSDKClient(options=options) as client:
        await client.query("50과 25를 더해주세요")
        async for msg in client.receive_response():
            print(msg)


if __name__ == "__main__":
    # 메인 함수 실행
    anyio.run(main)
    
    # 또는 standalone 사용 예제 실행
    # anyio.run(standalone_usage)