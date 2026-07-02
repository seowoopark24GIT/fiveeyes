"""약국 PC USB — Arduino UNO 시리얼 게이트웨이."""

from __future__ import annotations

import logging

import serial

from config import ARDUINO_BAUD, ARDUINO_PORT, ARDUINO_TIMEOUT_SEC
from services.hardware.protocol import LabelJobRequest, LabelJobResult, parse_response

logger = logging.getLogger(__name__)


def run_label_job(job: LabelJobRequest) -> LabelJobResult:
    """UNO에 JSON JOB 한 줄 전송 → JSON 응답 한 줄 대기."""
    if not ARDUINO_PORT:
        return LabelJobResult(
            False,
            False,
            "arduino",
            job_id=job.job_id,
            detail="ARDUINO_PORT가 설정되지 않았습니다. .env를 확인하세요.",
        )

    wire = job.to_wire()
    logger.info("[arduino] JOB 전송 port=%s job_id=%s", ARDUINO_PORT, job.job_id)

    try:
        with serial.Serial(
            port=ARDUINO_PORT,
            baudrate=ARDUINO_BAUD,
            timeout=ARDUINO_TIMEOUT_SEC,
        ) as ser:
            ser.reset_input_buffer()
            ser.write(wire.encode("utf-8"))
            ser.flush()

            response_line = ser.readline().decode("utf-8", errors="replace")
            result = parse_response(response_line, mode="arduino")
            result.job_id = result.job_id or job.job_id

            if result.ok:
                logger.info("[arduino] 완료 job_id=%s", job.job_id)
            else:
                logger.warning("[arduino] 실패 job_id=%s detail=%s", job.job_id, result.detail)

            return result

    except serial.SerialException as exc:
        logger.error("[arduino] 시리얼 오류 (%s): %s", ARDUINO_PORT, exc)
        return LabelJobResult(
            False,
            False,
            "arduino",
            job_id=job.job_id,
            detail=f"아두이노 연결 실패 ({ARDUINO_PORT}): {exc}",
        )
