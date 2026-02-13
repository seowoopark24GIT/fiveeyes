import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR,'pharmacy.db')}" #DB 파일 위치 

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} #DB랑 실제로 연결하는 엔진
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
) #DB를 쓰기 위한 접속권

Base = declarative_base() #DB 설계도 도화지 


