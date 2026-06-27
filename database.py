import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_default_sqlite = f"sqlite:///{os.path.join(BASE_DIR, 'pharmacy.db')}"
DATABASE_URL = os.getenv("DATABASE_URL", _default_sqlite)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
) #DB를 쓰기 위한 접속권

Base = declarative_base() #DB 설계도 도화지 


