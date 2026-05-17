import json
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal
from models import Medicine, User
from schemas import PharmacistGenerateRequest, PacketMedicineRequest
from services.braille import convert_to_braille
from services.mfds_api import search_drug_info, search_drug_info_smart, search_drug_appearance
from services.ai_service import analyze_drug, build_packet_voice_script
from services.printer import print_braille_label
from services.nfc_writer import write_nfc_url
from routers.auth import require_login
from config import BASE_URL

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/pharmacist", response_class=HTMLResponse)
def pharmacist_page(request: Request, user: User = Depends(require_login)):
    response = templates.TemplateResponse("pharmacist.html", {"request": request, "user": user})
    response.headers["Cache-Control"] = "no-store"
    return response


class SearchRequest(BaseModel):
    item_name: str


@router.post("/pharmacist/search")
async def search_drug(body: SearchRequest):
    """약 이름으로 식약처 API 조회 — 단계적 폴백 검색"""
    easy_list = await search_drug_info_smart(body.item_name)
    appearance = await search_drug_appearance(body.item_name)

    if not easy_list:
        raise HTTPException(status_code=404, detail="해당 약을 찾을 수 없습니다.")

    drug = easy_list[0]
    # DrbEasyDrugInfoService의 itemSeq 우선 사용 (medicine 페이지에서 같은 서비스로 재조회하므로)
    item_seq = drug.get("itemSeq") or (appearance.get("itemSeq") if appearance else None)
    return {
        "itemSeq": item_seq,
        "itemName": drug.get("itemName"),
        "efcyQesitm": drug.get("efcyQesitm"),
        "useMethodQesitm": drug.get("useMethodQesitm"),
        "atpnWarnQesitm": drug.get("atpnWarnQesitm"),
        "seQesitm": drug.get("seQesitm"),
        "itemImage": appearance.get("itemImage") if appearance else None,
        "drugShape": appearance.get("drugShape") if appearance else None,
        "colorClass1": appearance.get("colorClass1") if appearance else None,
        "markCode": appearance.get("markCode") if appearance else None,
    }


@router.get("/pharmacist/braille-preview")
def braille_preview(text: str):
    """점자 변환 미리보기 전용 — DB/하드웨어 조작 없음"""
    from services.braille import convert_to_braille
    return {"braille": convert_to_braille(text), "original": text}


@router.post("/pharmacist/generate")
async def generate_output(
    data: PharmacistGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_login),
):
    """점자 라벨 출력 + NFC 태그 쓰기 + DB 저장 + AI 음성 스크립트 생성"""

    medicine = db.query(Medicine).filter(
        Medicine.mfds_item_seq == data.item_seq
    ).first()

    drug_info_json = json.dumps(data.drug_data, ensure_ascii=False) if data.drug_data else None
    short_name = data.braille_text or data.item_name

    if not medicine:
        medicine = Medicine(
            name=data.item_name,
            short_name=short_name,
            mfds_item_seq=data.item_seq,
            pill_image_url=data.item_image,
            drug_info_json=drug_info_json,
        )
        db.add(medicine)
        db.flush()
    else:
        medicine.name = data.item_name
        medicine.short_name = short_name
        medicine.pill_image_url = data.item_image
        if drug_info_json:
            medicine.drug_info_json = drug_info_json

    # AI 음성 스크립트를 약사 generate 시점에 생성 (NFC 페이지는 캐시만 읽음)
    drug_info = data.drug_data or {}
    image_url = drug_info.get("itemImage") or data.item_image
    voice_script = await analyze_drug(drug_info, image_url, short_name)
    medicine.voice_script_json = json.dumps(voice_script, ensure_ascii=False)

    db.commit()
    db.refresh(medicine)

    braille_name = convert_to_braille(data.braille_text or data.item_name)
    nfc_url = f"{BASE_URL}/medicine/{data.item_seq}"

    printer_ok = print_braille_label(braille_name, data.item_name)
    nfc_ok = write_nfc_url(nfc_url)

    return {
        "success": True,
        "nfc_data": nfc_url,
        "braille_name": braille_name + data.item_name,
        "printer_ok": printer_ok,
        "nfc_ok": nfc_ok,
        "medicine_id": medicine.id,
        "voice_preview": voice_script[:2],  # 약사 화면에 미리보기용
    }


@router.post("/pharmacist/packet/generate")
async def generate_packet_output(
    data: PacketMedicineRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_login),
):
    """봉지약: 약사 직접 입력 → 음성 스크립트 생성 → NFC + 점자 출력"""
    item_seq = f"PKT-{uuid4().hex[:8]}"

    drug_items = [d.model_dump() for d in data.drugs]
    voice_script = build_packet_voice_script(
        label=data.label,
        purpose=data.purpose,
        timing=data.timing,
        drugs=drug_items,
        extra_caution=data.extra_caution,
    )

    medicine = Medicine(
        name=data.label,
        short_name=data.label,
        mfds_item_seq=item_seq,
        pill_image_url=data.item_image,
        is_packet=True,
        packet_items_json=json.dumps(drug_items, ensure_ascii=False),
        voice_script_json=json.dumps(voice_script, ensure_ascii=False),
    )
    db.add(medicine)
    db.commit()
    db.refresh(medicine)

    braille_name = convert_to_braille(data.label)
    nfc_url = f"{BASE_URL}/medicine/{item_seq}"

    printer_ok = print_braille_label(braille_name, data.label)
    nfc_ok = write_nfc_url(nfc_url)

    return {
        "success": True,
        "nfc_data": nfc_url,
        "item_seq": item_seq,
        "braille_name": braille_name + data.label,
        "printer_ok": printer_ok,
        "nfc_ok": nfc_ok,
        "medicine_id": medicine.id,
        "voice_preview": voice_script[:3],
    }
