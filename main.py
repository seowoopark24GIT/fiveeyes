from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import engine
from models import Base
from config import SECRET_KEY
from routers import auth, pharmacist, user
from routers.auth import LoginRequiredException

Base.metadata.create_all(bind=engine)

app = FastAPI(title="시각장애인 복약 AI 접근성 시스템")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.exception_handler(LoginRequiredException)
async def login_required_handler(_request: Request, _exc: LoginRequiredException):
    return RedirectResponse(url="/login", status_code=302)

app.include_router(auth.router)
app.include_router(pharmacist.router)
app.include_router(user.router)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
