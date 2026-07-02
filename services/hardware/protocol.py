"""Python ↔ Arduino UNO 시리얼 프로토콜 (JSON 한 줄)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass


@dataclass
class LabelJobRequest:
    braille: str
    nfc_url: str
    label: str
    job_id: str

    @classmethod
    def create(cls, *, braille: str, nfc_url: str, label: str, job_id: str | None = None) -> LabelJobRequest:
        return cls(
            braille=braille,
            nfc_url=nfc_url,
            label=label,
            job_id=job_id or uuid.uuid4().hex[:12],
        )

    def to_wire(self) -> str:
        payload = {
            "cmd": "label",
            "job_id": self.job_id,
            "braille": self.braille,
            "nfc_url": self.nfc_url,
            "label": self.label,
        }
        return json.dumps(payload, ensure_ascii=False) + "\n"


@dataclass
class LabelJobResult:
    braille_ok: bool
    nfc_ok: bool
    mode: str
    job_id: str = ""
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.braille_ok and self.nfc_ok


def parse_response(line: str, *, mode: str) -> LabelJobResult:
    line = line.strip()
    if not line:
        return LabelJobResult(False, False, mode, detail="빈 응답")

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return LabelJobResult(False, False, mode, detail=f"JSON 파싱 실패: {line[:120]}")

    status = data.get("status", "fail")
    ok = status == "ok"
    return LabelJobResult(
        braille_ok=bool(data.get("braille", ok)),
        nfc_ok=bool(data.get("nfc", ok)),
        mode=mode,
        job_id=str(data.get("job_id", "")),
        detail=str(data.get("msg", data.get("detail", ""))),
    )
