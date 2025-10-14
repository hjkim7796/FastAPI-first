"""
Math Operations MCP Server using Claude Agent SDK
계산기 기능을 제공하는 SDK MCP 서버
"""

import anyio
import json
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions
from typing import Optional
from session_manager import MultiSessionController
import os


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
    print(f"🔧 add called with args: {args}")
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

# Subtract 도구 정의
@tool(
    name="subtract",
    description="두 숫자를 뺍니다",
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
async def subtract(args):
    """두 숫자를 빼는 함수"""
    print(f"🔧 subtract called with args: {args}")
    a = args.get("a")
    b = args.get("b")
    
    if a is None or b is None:
        return {
            "content": [
                {"type": "text", "text": "오류: a와 b 파라미터가 필요합니다"}
            ],
            "isError": True
        }
    
    result = a - b
    return {
        "content": [
            {"type": "text", "text": f"{a} - {b} = {result}"}
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
    print(f"🔧 multiply called with args: {args}")
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

# Divide 도구 정의
@tool(
    name="divide",
    description="두 숫자를 나눕니다",
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
async def divide(args):
    """두 숫자를 나누는 함수"""
    print(f"🔧 divide called with args: {args}")
    a = args.get("a")
    b = args.get("b")
    
    if a is None or b is None:
        return {
            "content": [
                {"type": "text", "text": "오류: a와 b 파라미터가 필요합니다"}
            ],
            "isError": True
        }
    
    result = a / b
    return {
        "content": [
            {"type": "text", "text": f"{a} / {b} = {result}"}
        ]
    }

# SDK MCP 서버 생성
calc_server = create_sdk_mcp_server(
    name="calc",
    version="1.0.0",
    tools=[add, subtract, multiply, divide]
)

# 환경 변수 로드
print("BRAVE_API_KEY:", os.getenv("BRAVE_API_KEY") is not None)


# 전역 세션 매니저
_global_session_controller: Optional[MultiSessionController] = None
def get_session_controller() -> MultiSessionController:
    """전역 세션 컨트롤러를 가져오기"""
    global _global_session_controller
    if _global_session_controller is None:
        _global_session_controller = MultiSessionController()
    return _global_session_controller


async def ai_stream_generator(prompt: str, user_id: str):
    """
    Server-Sent Events (SSE) 방식으로 AI 쿼리를 처리하고 결과를 스트리밍
    """
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5-20250929",
        mcp_servers={
            "calc": calc_server,
            # "brave-search": {
            #     "command": "npx",
            #     "args": ["-y", "@brave/brave-search-mcp-server"],
            #     "env": {
            #         "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")
            #     }
            # },
        },
        allowed_tools=[
            "mcp__calc__add", 
            "mcp__calc__subtract",
            "mcp__calc__multiply", 
            "mcp__calc__divide",
            #"mcp__brave-search__brave_web_search",
            ],
        permission_mode="acceptEdits",
        system_prompt="당신의 수학 연산을 도와주는 AI 어시스턴트입니다.",
        resume=None,
    )
    _session_controller = get_session_controller()
    

    async for message in _session_controller.query(prompt,user_id,options):
        yield message

