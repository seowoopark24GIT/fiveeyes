from sqlalchemy import Column, Integer, String
from database import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True) #약 번호
    name = Column(String, index=True) #약 이름
    description = Column(String) #약 설명
    dosage = Column(String) #약 복용법
    caution = Column(String) #주의사항

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(String) #'admin' or 'pharmacist'

