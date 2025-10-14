"""
Claude Agent SDK - 세션 ID 기반 컨텍스트 유지

핵심: ClaudeAgentOptions에 resume 파라미터로 session_id를 전달해야 합니다!
"""

import asyncio
from typing import override, List, Dict, Any, Optional
import json
from claude_agent_sdk import ClaudeSDKClient, query
from claude_agent_sdk.types import SystemMessage, AssistantMessage, UserMessage, ResultMessage, TextBlock
from message_to_json import user_message_to_text

# ==================== Claude는 세션에서 이전 메시지를 기억합니다. ====================
# ClaudeAgentOptions.resume을 사용해야 한다.
# ================================================================================

class SessionManager:
    """
    세션 ID 기반 컨텍스트 관리 - 베이스 클래스
    """
    def __init__(self):
        self.session_id: Optional[str] = None

    async def query(self, prompt: str, options):
        pass
                    

    async def process_message(self, message: str):
        print(f"응답: {str(message)}\n")
        if isinstance(message, SystemMessage):
            if message.data['subtype'] == 'init': # and options.resume != message.data['session_id']:
                if self.session_id is None:
                    self.session_id = message.data['session_id']
                    print(f"📌 Session ID: {message.data['session_id']}")
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip() != "":
                    yield f"data: {json.dumps({'status': 'processing', 'result': block.text})}\n\n"
        elif isinstance(message, UserMessage):
            user_message = user_message_to_text(message)
            if user_message != "":
                yield f"data: {json.dumps({'status': 'processing', 'result': user_message})}\n\n"
        elif isinstance(message, ResultMessage):
            yield f"data: {json.dumps({'status': 'completed', 'result': message.result})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'processing', 'result': str(message)})}\n\n"

    def get_session_id(self) -> Optional[str]:
        """현재 세션 ID 반환"""
        return self.session_id
    
    def reset_session(self):
        """새 세션 시작 (컨텍스트 초기화)"""
        self.session_id = None
        print("✅ 세션이 초기화되었습니다.")
        
# ==================== ClaudeSDKClient 방식 ====================
class SessionManagerWithClient(SessionManager):
    """
    ClaudeSDKClient(연속적인 대화)를 사용해야 하는 경우
    최적:
        대화 이어가기 - Claude가 문맥을 기억해야 할 때(Continuing conversations - When you need Claude to remember context)
        후속 질문 - 이전 응답을 기반으로(Follow-up questions - Building on previous responses)
        대화형 애플리케이션 - 채팅 인터페이스, REPL(Interactive applications - Chat interfaces, REPLs)
        응답 기반 로직 - 다음 작업이 Claude의 응답에 따라 달라질 때(Response-driven logic - When next action depends on Claude’s response)
        세션 제어 - 대화 수명 주기를 명시적으로 관리(Session control - Managing conversation lifecycle explicitly)
    """
    def __init__(self):
        super().__init__()
    
    @override
    async def query(self, prompt: str, options):
        """
        세션 ID를 사용하여 쿼리 실행
        """
        
        options.resume = self.session_id  # 👈 이전 세션 ID 전달!
        
        # ClaudeSDKClient 사용
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            
            async for message in client.receive_response():
                async for msg in self.process_message(message):
                    yield msg

# ==================== Query 방식 ====================
class SessionManagerWithQuery(SessionManager):
    """
    When to Use query() (New Session Each Time)
    Best for:
        대화 기록이 필요 없는 일회성 질문(One-off questions where you don’t need conversation history)
        이전 교환의 컨텍스트가 필요 없는 독립적인 작업(Independent tasks that don’t require context from previous exchanges)
        간단한 자동화 스크립트(Simple automation scripts)
        매번 새로운 시작을 원할 때(When you want a fresh start each time)
    """
    def __init__(self):
        super().__init__()
    
    @override
    async def query(self, prompt: str, options):
        """
        세션 ID를 사용하여 컨텍스트 유지하며 쿼리 실행
        """
        
        options.resume = self.session_id  # 👈 이전 세션 ID 전달!
        
        # query() 함수 사용
        async for message in query(prompt=prompt, options=options):
            async for msg in self.process_message(message):
                yield msg
    
# ==================== 사용자별 세션 관리 ====================

class MultiSessionController:
    """
    여러 사용자의 독립적인 세션 관리
    """
    def __init__(self):
        self.sessions: Dict[str, SessionManager] = {}
    
    def get_or_create_session(self, user_id: str) -> SessionManager:
        """사용자 세션 가져오기 또는 생성"""
        print(f"🔑 user_id={user_id}")
        if user_id not in self.sessions:
            self.sessions[user_id] = SessionManagerWithClient()
            #self.sessions[user_id] = SessionManagerWithQuery()
        return self.sessions[user_id]
    
    async def query(self, prompt: str, user_id: str, options):
        """특정 사용자 세션에서 쿼리 실행"""
        session = self.get_or_create_session(user_id)
        async for message in session.query(prompt, options):
            yield message
    
    def reset_session(self, user_id: str):
        """특정 사용자 세션 초기화"""
        if user_id in self.sessions:
            self.sessions[user_id].reset_session()
    
    def get_session_info(self, user_id: str) -> Optional[str]:
        """세션 정보 조회"""
        if user_id in self.sessions:
            return self.sessions[user_id].get_session_id()
        return None

