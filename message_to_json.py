"""
claude_agent_sdk.types의 UserMessage를 JSON으로 변환
"""

import json
from typing import Dict, Any, List
from claude_agent_sdk.types import UserMessage

# ==================== 핵심 변환 함수 ====================

def user_message_to_json(user_message: UserMessage) -> str:
    """
    UserMessage를 JSON 문자열로 변환
    
    Args:
        user_message: UserMessage 객체
    
    Returns:
        JSON 문자열
    
    사용법:
        json_str = user_message_to_json(user_message)
        print(json_str)
    """
    # Pydantic v2
    if hasattr(user_message, 'model_dump_json'):
        return user_message.model_dump_json(indent=2)
    
    # Pydantic v1
    elif hasattr(user_message, 'json'):
        return user_message.json(indent=2, ensure_ascii=False)
    
    # Fallback
    else:
        data = user_message_to_dict(user_message)
        return json.dumps(data, ensure_ascii=False, indent=2)


def user_message_to_dict(user_message: UserMessage) -> Dict[str, Any]:
    """
    UserMessage를 딕셔너리로 변환
    
    Args:
        user_message: UserMessage 객체
    
    Returns:
        딕셔너리
    
    사용법:
        data = user_message_to_dict(user_message)
        print(data['role'])
        print(data['content'])
    """
    # Pydantic v2
    if hasattr(user_message, 'model_dump'):
        return user_message.model_dump()
    
    # Pydantic v1
    elif hasattr(user_message, 'dict'):
        return user_message.dict()
    
    # Fallback
    else:
        return {
            'role': getattr(user_message, 'role', 'user'),
            'content': getattr(user_message, 'content', ''),
        }


def user_message_to_text(user_message: UserMessage) -> str:
    """
    UserMessage에서 텍스트 내용만 추출
    
    Args:
        user_message: UserMessage 객체
    
    Returns:
        텍스트 내용
    
    사용법:
        text = user_message_to_text(user_message)
        print(text)
    """
    # content가 문자열인 경우
    if isinstance(user_message.content, str):
        return user_message.content
    
    # content가 리스트인 경우
    elif isinstance(user_message.content, list):
        texts = []
        for item in user_message.content:
            if isinstance(item, dict) and item.get('type') == 'text':
                texts.append(item.get('text', ''))
            elif hasattr(item, 'text'):
                texts.append(item.text)
        return '\n'.join(texts)
    
    # 기타
    else:
        return str(user_message.content)


# ==================== 여러 메시지 처리 ====================

def messages_to_json(messages: List[UserMessage]) -> str:
    """
    여러 UserMessage를 JSON 배열로 변환
    
    Args:
        messages: UserMessage 리스트
    
    Returns:
        JSON 문자열
    
    사용법:
        json_str = messages_to_json([msg1, msg2, msg3])
    """
    messages_data = [user_message_to_dict(msg) for msg in messages]
    return json.dumps(messages_data, ensure_ascii=False, indent=2)


def messages_to_list(messages: List[UserMessage]) -> List[Dict[str, Any]]:
    """
    여러 UserMessage를 딕셔너리 리스트로 변환
    
    Args:
        messages: UserMessage 리스트
    
    Returns:
        딕셔너리 리스트
    
    사용법:
        data_list = messages_to_list([msg1, msg2, msg3])
    """
    return [user_message_to_dict(msg) for msg in messages]


# ==================== 출력 및 저장 ====================

def print_user_message(user_message: UserMessage):
    """
    UserMessage를 보기 좋게 출력
    
    사용법:
        print_user_message(user_message)
    """
    print(f"\n{'='*60}")
    print(f"Role: {user_message.role}")
    print(f"{'='*60}")
    print(f"Content: {user_message_to_text(user_message)}")
    print(f"{'='*60}\n")


def save_user_message(user_message: UserMessage, filename: str = "user_message.json"):
    """
    UserMessage를 JSON 파일로 저장
    
    사용법:
        save_user_message(user_message, "output.json")
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(user_message_to_json(user_message))
    print(f"✅ 저장 완료: {filename}")


def save_messages(messages: List[UserMessage], filename: str = "messages.json"):
    """
    여러 UserMessage를 JSON 파일로 저장
    
    사용법:
        save_messages([msg1, msg2, msg3], "conversation.json")
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(messages_to_json(messages))
    print(f"✅ 저장 완료: {filename}")


# ==================== Claude SDK 통합 예시 ====================

async def process_user_messages():
    """
    Claude SDK에서 UserMessage 처리 예시
    """
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5-20250929",
    )
    
    user_messages = []
    
    async with ClaudeSDKClient(options=options) as client:
        # 사용자 메시지 생성
        await client.query("안녕하세요!")
        
        async for msg in client.receive_response():
            # UserMessage 타입 체크
            if isinstance(msg, UserMessage):
                # 방법 1: JSON으로 변환
                json_str = user_message_to_json(msg)
                print("JSON 변환:")
                print(json_str)
                
                # 방법 2: 딕셔너리로 변환
                data = user_message_to_dict(msg)
                print(f"\n딕셔너리: {data}")
                
                # 방법 3: 내용만 추출
                content = user_message_to_text(msg)
                print(f"\n내용: {content}")
                
                # 방법 4: 보기 좋게 출력
                print_user_message(msg)
                
                # 메시지 수집
                user_messages.append(msg)
        
        # 모든 메시지 저장
        if user_messages:
            save_messages(user_messages, "conversation_history.json")


# ==================== 대화 히스토리 관리 ====================

class ConversationHistory:
    """
    UserMessage 히스토리 관리 클래스
    """
    
    def __init__(self):
        self.messages: List[UserMessage] = []
    
    def add_message(self, user_message: UserMessage):
        """메시지 추가"""
        self.messages.append(user_message)
    
    def to_json(self) -> str:
        """전체 히스토리를 JSON으로 변환"""
        return messages_to_json(self.messages)
    
    def to_list(self) -> List[Dict[str, Any]]:
        """전체 히스토리를 리스트로 변환"""
        return messages_to_list(self.messages)
    
    def save(self, filename: str = "history.json"):
        """파일로 저장"""
        save_messages(self.messages, filename)
    
    def get_last_message(self) -> UserMessage:
        """마지막 메시지 반환"""
        return self.messages[-1] if self.messages else None
    
    def get_content_only(self) -> List[str]:
        """모든 메시지의 내용만 추출"""
        return [user_message_to_text(msg) for msg in self.messages]
    
    def clear(self):
        """히스토리 초기화"""
        self.messages.clear()


# ==================== 실전 사용 예시 ====================

async def example_usage():
    """
    실전 사용 예시
    """
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5-20250929",
    )
    
    # 대화 히스토리 관리
    history = ConversationHistory()
    
    async with ClaudeSDKClient(options=options) as client:
        # 사용자 메시지 전송
        await client.query("Python에서 JSON을 다루는 방법을 알려줘")
        
        async for msg in client.receive_response():
            if isinstance(msg, UserMessage):
                # 히스토리에 추가
                history.add_message(msg)
                
                # JSON으로 변환하여 로깅
                json_str = user_message_to_json(msg)
                print(f"[LOG] {json_str}")
        
        # 두 번째 메시지
        await client.query("좀 더 자세히 설명해줘")
        
        async for msg in client.receive_response():
            if isinstance(msg, UserMessage):
                history.add_message(msg)
        
        # 전체 대화 저장
        history.save("conversation.json")
        
        # 내용만 출력
        contents = history.get_content_only()
        print("\n=== 대화 내용 ===")
        for idx, content in enumerate(contents, 1):
            print(f"{idx}. {content}")


# ==================== 테스트 코드 ====================

def test_user_message_conversion():
    """
    UserMessage 변환 테스트
    """
    # 테스트용 UserMessage 생성
    test_message = UserMessage(
        role="user",
        content="안녕하세요! Python에 대해 알려주세요."
    )
    
    print("="*80)
    print("테스트 1: JSON 문자열 변환")
    print("="*80)
    json_str = user_message_to_json(test_message)
    print(json_str)
    
    print("\n" + "="*80)
    print("테스트 2: 딕셔너리 변환")
    print("="*80)
    data = user_message_to_dict(test_message)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    print("\n" + "="*80)
    print("테스트 3: 내용만 추출")
    print("="*80)
    content = user_message_to_text(test_message)
    print(content)
    
    print("\n" + "="*80)
    print("테스트 4: 보기 좋게 출력")
    print("="*80)
    print_user_message(test_message)
    
    print("="*80)
    print("테스트 5: 파일 저장")
    print("="*80)
    save_user_message(test_message, "test_user_message.json")


if __name__ == "__main__":
    test_user_message_conversion()