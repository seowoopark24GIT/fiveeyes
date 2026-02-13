#입력 데이터 형식 정의
from pydantic import BaseModel

class MedicineCreate(BaseModel): #API로 들어오는 데이터 규칙
    name: str
    description: str
    dosage: str
    caution: str

