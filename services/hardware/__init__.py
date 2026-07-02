"""점자 + NFC 하드웨어 출력 (mock 또는 Arduino UNO)."""

from config import HARDWARE_MODE
from services.hardware.protocol import LabelJobRequest, LabelJobResult
from services.hardware import mock, arduino_bridge


def dispatch_label_job(*, braille: str, nfc_url: str, label: str) -> LabelJobResult:
    """HARDWARE_MODE에 따라 mock 또는 arduino_bridge 실행."""
    job = LabelJobRequest.create(braille=braille, nfc_url=nfc_url, label=label)

    if HARDWARE_MODE == "arduino":
        return arduino_bridge.run_label_job(job)

    return mock.run_label_job(job)
