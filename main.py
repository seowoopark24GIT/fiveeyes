from fastapi import FastAPI, Depends, HTTPException, Query, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, SessionLocal
from models import Base, Medicine, User
from schemas import MedicineCreate
from pydantic import BaseModel

from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware

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
# 비밀번호 설정
# =========================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

import unicodedata
# =========================
# 점자 세팅
# =========================
# 점자 매핑 테이블(한글 -> 초성/ 중성/ 종성 분해)
CHO_LIST = [
    "ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ",
    "ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"
]

JUNG_LIST = [
    "ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ",
    "ㅗ","ㅘ","ㅙ","ㅚ","ㅛ",
    "ㅜ","ㅝ","ㅞ","ㅟ","ㅠ",
    "ㅡ","ㅢ","ㅣ"
]

JONG_LIST = [
    "","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ",
    "ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ",
    "ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ",
    "ㅋ","ㅌ","ㅍ","ㅎ"
]

BRAILLE = {
    "ㄱ":"⠈","ㄴ":"⠉","ㄷ":"⠊","ㄹ":"⠐",
    "ㅁ":"⠑","ㅂ":"⠘","ㅅ":"⠠","ㅇ":"⠛",
    "ㅈ":"⠨","ㅊ":"⠰","ㅋ":"⠋","ㅌ":"⠓",
    "ㅍ":"⠙","ㅎ":"⠚",

    "ㅏ":"⠣","ㅑ":"⠜","ㅓ":"⠎","ㅕ":"⠱",
    "ㅗ":"⠥","ㅛ":"⠬","ㅜ":"⠍","ㅠ":"⠩",
    "ㅡ":"⠪","ㅣ":"⠕",

    "ㄱ_종":"⠁","ㄴ_종":"⠒","ㄷ_종":"⠔","ㄹ_종":"⠂",
    "ㅁ_종":"⠢","ㅂ_종":"⠃","ㅅ_종":"⠄","ㅇ_종":"⠶"
}

def decompose_hangul(char): # 한글 분해 함수
    code = ord(char) - 0xAC00
    cho = code // 588
    jung = (code % 588) // 28
    jong = code % 28
    return CHO_LIST[cho], JUNG_LIST[jung], JONG_LIST[jong]

def convert_to_braille(text: str):
    result = ""

    for char in text:
        # 한글 음절 범위 체크
        if 0xAC00 <= ord(char) <= 0xD7A3:
            cho, jung, jong = decompose_hangul(char)

            # 초성
            result += BRAILLE.get(cho, "")

            # 중성
            result += BRAILLE.get(jung, "")

            # 종성
            if jong:
                result += BRAILLE.get(jong + "_종", "")

        else:
            result += char  # 한글 아니면 그대로

    return result

# =========================
# 앱 생성 + 세션 미들웨어
# =========================
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

templates = Jinja2Templates(directory="templates")

# =========================
# 세션 기반 사용자 확인
# =========================
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    username = request.session.get("user")

    if not username:
        raise HTTPException(status_code=401)

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=401)

    return user

def admin_only(
    request: Request,
    db: Session = Depends(get_db)
):
    username = request.session.get("user")

    if not username:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.username == username).first()

    if not user or user.role != "admin":
        return RedirectResponse(url="/login", status_code=302)

    return user

# =========================
# INDEX
# =========================
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# =========================
# 로그인 페이지
# =========================
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

# =========================
# 로그인 처리 (세션 저장)
# =========================
class LoginRequest(BaseModel):
    username: str
    password: str

from fastapi import Form

@app.post("/auth/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse(url="/login?error=1", status_code=302)

    request.session["user"] = user.username

    return RedirectResponse(url="/admin", status_code=302)

# =========================
# 로그아웃
# =========================
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

# =========================
# 관리자 페이지 (보호)
# =========================
@app.get("/admin", response_class=HTMLResponse)
def admin_page(
    request: Request,
    user: User = Depends(admin_only)
):
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )

# =========================
# 약사용 페이지 (오픈)
# =========================
@app.get("/pharmacy", response_class=HTMLResponse)
def pharmacy_page(request: Request):
    return templates.TemplateResponse(
        "pharmacy.html",
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
# 검색
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
# 전체 조회
# =========================
@app.get("/medicines")
def get_medicines(db: Session = Depends(get_db)):
    return db.query(Medicine).all()

# =========================
# 단건 조회
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
    description: str | None = None
    dosage: str
    caution: str

@app.put("/medicines/{id}")
def update_medicine(
    id: int,
    request: Request,
    data: MedicineUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only)
):
    med = db.query(Medicine).filter(Medicine.id == id).first()

    if not med:
        raise HTTPException(status_code=404)

    med.name = data.name
    med.description = data.description
    med.dosage = data.dosage
    med.caution = data.caution

    db.commit()
    db.refresh(med)

    return {"message": "updated"}

# =========================
# 삭제
# =========================
@app.delete("/medicines/{id}")
def delete_medicine(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only)
):
    med = db.query(Medicine).filter(Medicine.id == id).first()

    if not med:
        raise HTTPException(status_code=404)

    db.delete(med)
    db.commit()

    return {"message": "deleted"}

# =========================
# 관리자 계정 생성
# =========================
@app.get("/create-admin")
def create_admin(db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == "admin").first()

    if existing:
        return {"message": "admin already exists"}

    hashed = hash_password("1234")

    admin = User(
        username="admin",
        hashed_password=hashed,
        role="admin"
    )

    db.add(admin)
    db.commit()

    return {"message": "admin created"}

from pydantic import BaseModel

class PharmacyGenerateRequest(BaseModel):
    name: str
    description: str | None = None
    dosage: str
    caution: str

# =========================
# 약사 페이지 출력 생성
# =========================
@app.post("/pharmacy/generate")
def generate_pharmacy_output(data: PharmacyGenerateRequest):

    nfc_data = f"""
약 이름: {data.name}
설명: {data.description}
복용방법: {data.dosage}
주의사항: {data.caution}
""".strip()

    braille_name = convert_to_braille(data.name)

    return {
        "nfc_data": nfc_data,
        "braille_name": braille_name + data.name
    }