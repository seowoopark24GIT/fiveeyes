import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MFDS_API_KEY = os.getenv("MFDS_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# 하드웨어: mock(기본) | arduino (약국 PC + UNO USB)
HARDWARE_MODE = os.getenv("HARDWARE_MODE", "mock").strip().lower()
ARDUINO_PORT = os.getenv("ARDUINO_PORT", "").strip()
ARDUINO_BAUD = int(os.getenv("ARDUINO_BAUD", "9600"))
ARDUINO_TIMEOUT_SEC = float(os.getenv("ARDUINO_TIMEOUT_SEC", "120"))

# 레거시 (직접 COM 프린터/NFC — arduino 모드 사용 권장)
BRAILLE_PRINTER_PORT = os.getenv("BRAILLE_PRINTER_PORT", "COM3")
NFC_WRITER_PORT = os.getenv("NFC_WRITER_PORT", "COM4")
