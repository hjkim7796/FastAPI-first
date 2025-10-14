from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator

# MySQL 연결 설정
DATABASE_URL = "mysql+pymysql://ddm:EoflowDDM$0200@localhost:3306/py_db"
# 형식: mysql+pymysql://사용자명:비밀번호@호스트:포트/데이터베이스명

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=3600,   # 1시간마다 연결 재활용
    echo=True            # SQL 쿼리 로깅 (개발 시에만)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 최신 방식의 Base 클래스
class Base(DeclarativeBase):
    pass

# 데이터베이스 세션 의존성
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()