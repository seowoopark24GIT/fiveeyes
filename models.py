from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)               # 약 이름
    mfds_item_seq = Column(String, unique=True)     # 식약처 품목일련번호 (NFC URL key)
    short_name = Column(String, nullable=True)         # 약사가 입력한 짧은 검색어 (예: 아스피린)
    pill_image_url = Column(String, nullable=True)     # 식약처 알약 이미지 URL
    drug_info_json = Column(String, nullable=True)     # 약사 검색 시 캐시된 약 정보 (JSON)
    voice_script_json = Column(String, nullable=True)  # 캐시된 AI 음성 안내 스크립트 (JSON)
    is_packet = Column(Boolean, default=False)          # 봉지약 여부
    packet_items_json = Column(String, nullable=True)  # 봉지약 구성 약 목록 (JSON)

    # 하위호환 필드 (기존 데이터 유지용)
    description = Column(String, nullable=True)
    dosage = Column(String, nullable=True)
    caution = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(String)  # 'admin' or 'pharmacist'
