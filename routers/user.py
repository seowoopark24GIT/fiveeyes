import json
import re
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import Depends

from database import SessionLocal
from models import Medicine
from services.mfds_api import search_drug_info, search_drug_appearance, get_drug_by_item_seq

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def _search_by_name_variants(full_name: str) -> dict | None:
    """약 이름을 단계적으로 짧게 줄여 MFDS API 재시도.
    예: "베노믹스아스피린장용캡슐100밀리그램(아스피린)"
     → "베노믹스아스피린장용캡슐" → "아스피린" 순서로 시도
    """
    candidates: list[str] = [full_name]

    # 숫자 이전까지 (예: "베노믹스아스피린장용캡슐100..." → "베노믹스아스피린장용캡슐")
    short = re.split(r'\d', full_name)[0].strip()
    if short and short != full_name:
        candidates.append(short)

    # 마지막 괄호 안 성분명 (예: "(아스피린)" → "아스피린")
    m = re.search(r'\(([^)]+)\)\s*$', full_name)
    if m:
        candidates.append(m.group(1).strip())

    for name in candidates:
        drug_list = await search_drug_info(name)
        if drug_list:
            return drug_list[0]
    return None


@router.get("/medicine/{item_seq}", response_class=HTMLResponse)
async def medicine_page(item_seq: str, request: Request, db: Session = Depends(get_db)):
    """NFC 탭 시 열리는 시각장애인용 음성 안내 페이지 — 캐시만 읽음, AI 재생성 없음"""

    medicine = db.query(Medicine).filter(Medicine.mfds_item_seq == item_seq).first()

    if not medicine or not medicine.voice_script_json:
        raise HTTPException(status_code=404, detail="약사가 아직 이 약의 라벨을 생성하지 않았습니다.")

    voice_script = json.loads(medicine.voice_script_json)
    item_name = medicine.short_name or medicine.name
    item_image = medicine.pill_image_url

    return templates.TemplateResponse("medicine.html", {
        "request": request,
        "item_name": item_name,
        "item_seq": item_seq,
        "item_image": item_image,
        "voice_script": voice_script,
        "voice_script_json": json.dumps(voice_script, ensure_ascii=False),
    })


@router.get("/api/medicine/{item_seq}")
async def medicine_api(item_seq: str, db: Session = Depends(get_db)):
    """모바일 앱 확장을 위한 JSON API"""
    medicine = db.query(Medicine).filter(Medicine.mfds_item_seq == item_seq).first()

    if medicine and medicine.voice_script_json:
        return {
            "itemSeq": item_seq,
            "itemName": medicine.name,
            "itemImage": medicine.pill_image_url,
            "voiceScript": json.loads(medicine.voice_script_json),
        }

    drug_info = await get_drug_by_item_seq(item_seq)
    if not drug_info:
        raise HTTPException(status_code=404, detail="의약품 정보를 찾을 수 없습니다.")

    appearance = await search_drug_appearance(drug_info.get("itemName", ""))
    item_image = appearance.get("itemImage") if appearance else None
    voice_script = await analyze_drug(drug_info, item_image)

    return {
        "itemSeq": item_seq,
        "itemName": drug_info.get("itemName"),
        "itemImage": item_image,
        "voiceScript": voice_script,
    }
