from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
from models import User
from schemas import UserCreate, UserUpdate 
from security import get_password_hash, verify_password
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
# from models import User
# from security import get_password_hash, verify_password

# 사용자 조회 (ID)
def get_user(db: Session, user_id: int) -> Optional[User]:
    """ID로 사용자를 조회합니다."""
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()

# 사용자 조회 (Email)
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """이메일로 사용자를 조회합니다."""
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()

# 사용자 조회 (Username)
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """사용자명으로 사용자를 조회합니다."""
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalar_one_or_none()

# 모든 사용자 조회
def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """모든 사용자 목록을 조회합니다."""
    stmt = select(User).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())

# 활성 사용자만 조회
def get_active_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """활성 사용자 목록을 조회합니다."""
    stmt = select(User).where(User.is_active == True).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())

# 사용자 생성
def create_user(db: Session, user: UserCreate) -> User:
    """새로운 사용자를 생성합니다."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 사용자 업데이트
def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """사용자 정보를 업데이트합니다."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

# 사용자 삭제
def delete_user(db: Session, user_id: int) -> bool:
    """사용자를 삭제합니다."""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

# 사용자 인증
def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """사용자 인증을 수행합니다."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# 사용자 수 조회
def get_users_count(db: Session) -> int:
    """전체 사용자 수를 조회합니다."""
    from sqlalchemy import func
    stmt = select(func.count(User.id))
    return db.execute(stmt).scalar()
