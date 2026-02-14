from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, SessionLocal
from models import Base, Medicine
from schemas import MedicineCreate
from pydantic import BaseModel

app = FastAPI()

# =========================
# DB 세팅
# =========================
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# 관리자 로그인
# =========================
security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "seowoo" or credentials.password != "0224":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

# =========================
# 관리자 페이지
# =========================
templates = Jinja2Templates(directory="templates")

@app.get("/admin", response_class=HTMLResponse)
def admin_page(
    request: Request,
    user: str = Depends(verify_admin)
):
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )

# =========================
# 약 추가
# =========================
@app.post("/medicines")
def create_medicine(
    medicine: MedicineCreate,
    db: Session = Depends(get_db)
):
    new_medicine = Medicine(
        name=medicine.name,
        description=medicine.description,
        dosage=medicine.dosage,
        caution=medicine.caution
    )
    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)
    return new_medicine


# =========================
# 검색 API
# =========================
@app.get("/medicines/search")
def search_medicines(
    name: str = Query(...),
    db: Session = Depends(get_db)
):
    medicines = db.query(Medicine).filter(
        func.lower(Medicine.name).contains(name.lower())
    ).all()
    return medicines

# =========================
# 전체 목록 조회
# =========================
@app.get("/medicines")
def get_medicines(db: Session = Depends(get_db)):
    return db.query(Medicine).all()


# =========================
# ID 조회
# =========================
@app.get("/medicines/{medicine_id}")
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if not medicine:
        raise HTTPException(status_code=404, detail="약을 찾을 수 없습니다")

    return medicine

# =========================
# 수정
# =========================
class MedicineUpdate(BaseModel):
    name: str
    description: str
    dosage: str
    caution: str

@app.put("/medicines/{medicine_id}")
def update_medicine(
    medicine_id: int,
    updated: MedicineUpdate,
    db: Session = Depends(get_db)
):
    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if not medicine:
        raise HTTPException(status_code=404, detail="약을 찾을 수 없습니다")

    medicine.name = updated.name
    medicine.description = updated.description
    medicine.dosage = updated.dosage
    medicine.caution = updated.caution

    db.commit()
    db.refresh(medicine)
    return medicine

# =========================
# 삭제
# =========================
@app.delete("/medicines/{medicine_id}")
def delete_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if not medicine:
        raise HTTPException(status_code=404, detail="약을 찾을 수 없습니다")

    db.delete(medicine)
    db.commit()

    return {"message": "삭제 완료"}