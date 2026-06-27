from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import SessionLocal
from models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    username = request.session.get("user")
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()


class LoginRequiredException(Exception):
    pass


def require_login(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise LoginRequiredException()
    return user


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/auth/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()
    if len(password) < 6:
        return RedirectResponse(url="/register?error=short", status_code=302)
    if password != password_confirm:
        return RedirectResponse(url="/register?error=mismatch", status_code=302)
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse(url="/register?error=exists", status_code=302)

    user = User(
        username=username,
        hashed_password=hash_password(password),
        role="pharmacist",
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login?registered=1", status_code=302)


@router.post("/auth/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse(url="/login?error=1", status_code=302)
    request.session["user"] = user.username
    return RedirectResponse(url="/pharmacist", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


