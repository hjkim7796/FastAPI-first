from dotenv import load_dotenv
import os
# 환경 변수 로드
load_dotenv()
print("ANTHROPIC_API_KEY:", os.getenv("ANTHROPIC_API_KEY") is not None)

from fastapi import FastAPI, Depends, HTTPException, status, Query, WebSocket, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Annotated, Dict, Any
from contextlib import asynccontextmanager
from pydantic import EmailStr, BaseModel, Field
from datetime import timedelta
from security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from database import Base, engine, get_db
from models import User
from generator import ai_stream_generator
import uvicorn


from schemas import UserCreate, UserUpdate, UserResponse, UserLogin, LoginResponse, MessageResponse
from crud import (
    get_user, get_user_by_email, get_user_by_username,
    get_users, get_active_users, create_user, update_user,
    delete_user, authenticate_user, get_users_count
)
from dependencies import get_current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 데이터베이스 테이블 생성
    Base.metadata.create_all(bind=engine)
    yield
    # 종료 시 정리 작업 (필요한 경우)

# Initialize FastAPI app
app = FastAPI(
    title="Users API with OAuth Token",
    description="FastAPI + MySQL + JWT OAuth Token + Claude Agent SDK을 사용한 사용자 관리 API",
    version="1.0.0",
    lifespan=lifespan,
    debug=True
)
# static 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize MCP
#mcp = FastApiMCP(app, name="fastmcp-http")
#mcp.mount(mount_path="/mcp")

# templates 폴더 설정
templates = Jinja2Templates(directory="templates")

# 의존성 주입 타입
DbDependency = Annotated[Session, Depends(get_db)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]

# ==================== REGULAR FASTAPI ENDPOINTS ====================
# These are standard REST API endpoints
# ===================================================================   
# 헬스 체크
@app.get("/", response_model=MessageResponse, tags=["Health"])
def root():
    """API 상태를 확인합니다."""
    return {"message": "Users API with OAuth Token is running"}

# 통계 정보
@app.get("/api/stats", tags=["Stats"])
def get_stats(db: DbDependency):
    """사용자 통계를 조회합니다."""
    total_users = get_users_count(db)
    return {
        "total_users": total_users,
        "api_version": "2.0.0",
        "token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES
    }

# 모든 사용자 조회
@app.get("/api/users", response_model=List[UserResponse], tags=["Users"])
def get_all_users(
    db: DbDependency,
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 최대 레코드 수"),
    active_only: bool = Query(False, description="활성 사용자만 조회")
):
    """
    모든 사용자 목록을 조회합니다.
    """
    if active_only:
        users = get_active_users(db, skip=skip, limit=limit)
    else:
        users = get_users(db, skip=skip, limit=limit)
    return users

# 특정 사용자 조회
@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user_by(user_id: int, db: DbDependency):
    """
    ID로 특정 사용자를 조회합니다.
    사용자 ID는 경로 매개변수로 전달됩니다.
    """
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return db_user

# 사용자 생성
@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"]
)
def create_new_user(user: UserCreate, db: DbDependency):
    """새로운 사용자를 생성합니다."""
    # 이메일 중복 체크
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )
    
    # 사용자명 중복 체크
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 사용자명입니다."
        )
    
    return create_user(db=db, user=user)

# 사용자 업데이트 (인증 필요)
@app.put("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_existing_user(
    user_id: int,
    user_update: UserUpdate,
    db: DbDependency,
    current_user: CurrentUserDependency  # 토큰 인증 필요
):
    """
    기존 사용자 정보를 업데이트합니다.
    
    **인증 필요**: Authorization 헤더에 Bearer 토큰이 필요합니다.
    
    사용자는 자신의 정보만 수정할 수 있습니다 (관리자 제외).
    """
    # 본인 확인 (관리자는 모든 사용자 수정 가능)
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 정보만 수정할 수 있습니다."
        )
    
    # 이메일 중복 체크 (자신 제외)
    if user_update.email:
        existing_user = get_user_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 이메일입니다."
            )
    
    # 사용자명 중복 체크 (자신 제외)
    if user_update.username:
        existing_user = get_user_by_username(db, username=user_update.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 사용자명입니다."
            )
    
    db_user = update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return db_user

# 사용자 삭제
@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
def delete_existing_user(user_id: int, db: DbDependency):
    """사용자를 삭제합니다."""
    success = delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return None

# 사용자 로그인 (OAuth 토큰 발급)
@app.post("/api/login", response_model=LoginResponse, tags=["Authentication"])
def login(user_login: UserLogin, db: DbDependency):
    """
    사용자 로그인을 처리하고 JWT 액세스 토큰을 발급합니다.
    
    토큰 유효기간: 5분
    """
    user = authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다."
        )
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "message": "로그인 성공",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name
        },
        "token": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 초 단위
        }
    }

# 현재 로그인한 사용자 정보 조회
@app.get("/api/me", response_model=UserResponse, tags=["Authentication"])
def read_current_user(current_user: CurrentUserDependency):
    """
    현재 로그인한 사용자의 정보를 조회합니다.
    
    **인증 필요**: Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    return current_user

# 이메일로 사용자 검색
@app.get("/api/users/search/by-email", response_model=UserResponse, tags=["Search"])
def search_user_by_email(email: EmailStr, db: DbDependency):
    """이메일로 사용자를 검색합니다."""
    db_user = get_user_by_email(db, email=email)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return db_user

# 사용자명으로 사용자 검색
@app.get("/api/users/search/by-username", response_model=UserResponse, tags=["Search"])
def search_user_by_username(username: str, db: DbDependency):
    """사용자명으로 사용자를 검색합니다."""
    db_user = get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return db_user

# AI Query - Server-Sent Events (SSE)
@app.get("/api/mcp/query-sse", response_model=List[str], tags=["AI"])
async def query_stream(query:str, user_id: str):
    """AI 로부터 Server-Sent Events (SSE) 방식으로 query를 수행한다."""
    return StreamingResponse(
        ai_stream_generator(query, user_id),
        media_type="text/event-stream"
    ) 

# ==================== REGULAR FASTAPI ENDPOINTS ====================
# Web 페이지 라우트 (테스트용)
# ===================================================================   
# 
@app.get("/sse", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse("sse_client.html", {
        "request": request,
        "title": "AI Query Client - Server-Sent Events (SSE)",
    })
# ==================== MAIN ====================
if __name__ == "__main__":
    print("Starting FastAPI Server...")
    print("API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        root_path="/ai",
        log_level="debug"
    )