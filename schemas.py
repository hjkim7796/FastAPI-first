from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

# 기본 사용자 스키마
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None

# 사용자 생성 스키마
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

# 사용자 업데이트 스키마
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    is_active: Optional[bool] = None

# 사용자 응답 스키마
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# 로그인 스키마
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 토큰 스키마
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# 토큰 데이터 스키마
class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

# 로그인 응답 스키마
class LoginResponse(BaseModel):
    message: str
    user: dict
    token: Token

# 메시지 응답 스키마
class MessageResponse(BaseModel):
    message: str