from  fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models import Base, Medicine
from schemas import MedicineCreate
from fastapi import Query # 약 검색

# HTML 추가할 라이브러리
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel # 약 정보 수정
class MedicineUpdate(BaseModel):
    name: str
    description: str
    dosage: str
    caution: str

app = FastAPI()  #API 서버

Base.metadata.create_all(bind=engine) #DB 테이블 생성

def get_db(): #DB 세션 의존성 
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#약 추가 API
@app.post("/medicines") #/medicines 주소
def create_medicine(
    medicine: MedicineCreate, #요청 JSON를 schemas.py 규칙으로 검사
    db: Session = Depends(get_db) #DB 장부 열기
):
    new_medicine = Medicine( #실제 데이터 객체 생성
        name=medicine.name,
        description=medicine.description,
        dosage=medicine.dosage,
        caution=medicine.caution
    )
    db.add(new_medicine) #저장할 목록에 올림
    db.commit() #진짜로 저장
    db.refresh(new_medicine) #DB가 준 id값 다시 가져오기

    return new_medicine

# 전체 약 몰록 조회
@app.get("/medicines")
def get_medicines(db: Session = Depends(get_db)):
    medicines = db.query(Medicine).all()
    return medicines

# 이름으로 약 조회
@app.get("/medicines/search")
def search_medicines(
    name: str = Query(..., description="약 이름 검색어"),
    db: Session = Depends(get_db)
):
    medicines = db.query(Medicine).filter(
        Medicine.name.contains(name)
    ).all()
    return medicines

# 특정 약 조회(id 기준)
@app.get("/medicines/{medicine_id}")
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        return {"error": "약을 찾을 수 없습니다"}
    return medicine

# 특정 약 삭제
@app.delete("/medicines/{medicine_id}")
def delete_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        return {"error": "약을 찾을 수 없습니다"}
    db.delete(medicine)
    db.commit()
    return {"message": "삭제 완료"}

# 특정 약 수정
@app.put("/medicines/{medicine_id}")
def update_medicine(
        medicine_id: int,
        updated: MedicineUpdate,
        db: Session = Depends(get_db)
):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        return {"error": "약을 찾을 수 없습니다"}
    medicine.name = updated.name
    medicine.description = updated.description
    medicine.dosage = updated.dosage
    medicine.caution = updated.caution
    db.commit()
    db.refresh(medicine)
    return medicine

#관리자 페이지
templates = Jinja2Templates(directory = "templates")
#관리자 페이지 API추가
@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )



