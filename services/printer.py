import serial
import logging
from config import BRAILLE_PRINTER_PORT

logger = logging.getLogger(__name__)


def print_braille_label(braille_text: str, drug_name: str) -> bool:
    """USB 점자 엠보서로 라벨 출력.

    엠보서 모델에 따라 명령어가 다를 수 있음.
    현재는 시리얼 포트로 텍스트 전송하는 범용 구현.
    실제 사용 시 엠보서 제조사 매뉴얼 참고 필요.
    """
    try:
        with serial.Serial(
            port=BRAILLE_PRINTER_PORT,
            baudrate=9600,
            timeout=5,
        ) as ser:
            payload = f"{braille_text}\r\n{drug_name}\r\n\x0C"  # \x0C = form feed (인쇄 시작)
            ser.write(payload.encode("utf-8"))
            ser.flush()
        logger.info("점자 라벨 출력 완료: %s", drug_name)
        return True
    except serial.SerialException as e:
        logger.error("점자 프린터 연결 실패 (%s): %s", BRAILLE_PRINTER_PORT, e)
        return False
