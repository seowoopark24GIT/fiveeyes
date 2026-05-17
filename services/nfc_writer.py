import logging

logger = logging.getLogger(__name__)

try:
    import nfc  # nfcpy 라이브러리 (pip install nfcpy)
    _NFC_AVAILABLE = True
except ImportError:
    _NFC_AVAILABLE = False
    logger.info("nfcpy 미설치: NFC 쓰기 기능 비활성화 (NFC 라이터 연결 시 pip install nfcpy)")


def write_nfc_url(url: str) -> bool:
    """USB NFC 라이터로 NDEF URL 레코드 기록.

    ACR122U 등 nfcpy 지원 NFC 리더/라이터 필요.
    태그를 라이터에 올려놓은 상태에서 호출하세요.
    """
    if not _NFC_AVAILABLE:
        logger.error("nfcpy 미설치로 NFC 쓰기 불가")
        return False

    try:
        with nfc.ContactlessFrontend("usb") as clf:
            tag = clf.connect(rdwr={"on-connect": lambda tag: False})
            if tag is None:
                logger.error("NFC 태그를 찾을 수 없습니다")
                return False

            record = nfc.ndef.UriRecord(url)
            message = nfc.ndef.Message(record)
            tag.ndef.records = message.records
            tag.ndef.length = len(message)
        logger.info("NFC 쓰기 완료: %s", url)
        return True
    except Exception as e:
        logger.error("NFC 쓰기 실패: %s", e)
        return False
