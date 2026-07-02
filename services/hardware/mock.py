"""하드웨어 없이 동작 — Render·로컬 개발·아두이노 미연결 시."""

import logging

from services.hardware.protocol import LabelJobRequest, LabelJobResult

logger = logging.getLogger(__name__)


def run_label_job(job: LabelJobRequest) -> LabelJobResult:
    logger.info(
        "[mock] 점자+NFC 시뮬레이션 | label=%s nfc_url=%s braille_len=%d",
        job.label,
        job.nfc_url,
        len(job.braille),
    )
    return LabelJobResult(
        braille_ok=True,
        nfc_ok=True,
        mode="mock",
        job_id=job.job_id,
        detail="하드웨어 미연결(mock). URL·점자는 서버에서 생성됨.",
    )
