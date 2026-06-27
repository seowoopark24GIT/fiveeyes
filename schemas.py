from pydantic import BaseModel


# ── 약사용 ──────────────────────────────────────────────────────────────

class PharmacistSearchRequest(BaseModel):
    item_name: str


class PharmacistGenerateRequest(BaseModel):
    item_seq: str
    item_name: str
    item_image: str | None = None
    braille_text: str | None = None  # 약사가 입력한 짧은 검색어 (점자 출력용)
    drug_data: dict | None = None    # 검색 결과 전체 캐시 (medicine 페이지 API 재호출 방지)


class IdentifyRequest(BaseModel):
    image_base64: str

# ── 봉지약용 ──────────────────────────────────────────────────────────────

class PacketDrug(BaseModel):
    name: str
    count: int
    item_seq: str | None = None
    efficacy: str | None = None
    caution: str | None = None


class PacketMedicineRequest(BaseModel):
    label: str                         # 봉지 라벨 (점자용, 예: "감기약")
    purpose: str                       # 전체 목적 (약사 타이핑)
    timing: str | None = None          # 복용 시간대 (예: "아침 식후")
    drugs: list[PacketDrug]
    extra_caution: str | None = None   # 약사 추가 주의사항
    item_image: str | None = None


# ── 사용자용 ─────────────────────────────────────────────────────────────

class MedicineVoiceResponse(BaseModel):
    item_seq: str
    item_name: str
    item_image: str | None
    voice_script: list[str]


# ── 하위호환 (기존 API 유지) ───────────────────────────────────────────────

class MedicineCreate(BaseModel):
    name: str
    description: str
    dosage: str
    caution: str


class PharmacyGenerateRequest(BaseModel):
    name: str
    description: str | None = None
    dosage: str
    caution: str
