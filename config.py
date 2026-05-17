import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MFDS_API_KEY = os.getenv("MFDS_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

BRAILLE_PRINTER_PORT = os.getenv("BRAILLE_PRINTER_PORT", "COM3")
NFC_WRITER_PORT = os.getenv("NFC_WRITER_PORT", "COM4")
