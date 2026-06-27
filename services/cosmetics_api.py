import httpx
from config import MFDS_API_KEY

_BASE = "http://apis.data.go.kr/1471000"

# 공공데이터포털: 기능성화장품 보고품목정보
# https://www.data.go.kr/data/15095680/openapi.do


async def search_cosmetic_info(item_name: str) -> list[dict]:
    """기능성화장품 보고품목정보 조회 (품목명 검색)"""
    url = f"{_BASE}/FtnltCosmRptPrdlstInfoService/getRptPrdlstInq"
    params = {
        "serviceKey": MFDS_API_KEY,
        "item_name": item_name,
        "type": "json",
        "numOfRows": 5,
        "pageNo": 1,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    body = data.get("body", {})
    items = body.get("items", [])
    if not items:
        return []
    return items if isinstance(items, list) else [items]


def normalize_cosmetic_item(item: dict) -> dict:
    """API 응답을 앱 내부 공통 형식으로 변환"""
    item_seq = item.get("ITEM_SEQ") or item.get("itemSeq")
    return {
        "productType": "cosmetic",
        "itemSeq": f"COS-{item_seq}" if item_seq else None,
        "itemName": item.get("ITEM_NAME") or item.get("itemName") or "",
        "manufacturer": item.get("ENTP_NAME") or item.get("entpName") or "",
        "reportDate": item.get("REPORT_DT") or item.get("reportDt") or "",
        "caution": item.get("CAUTION") or item.get("caution") or "",
        "usage": item.get("MAIN_INGR") or item.get("mainIngr") or "",
        "efcyQesitm": item.get("ITEM_NAME") or item.get("itemName") or "",
        "useMethodQesitm": "제품 라벨의 사용법을 확인하세요.",
        "atpnWarnQesitm": item.get("CAUTION") or item.get("caution") or "사용 전 패치 테스트를 권장합니다.",
        "seQesitm": None,
        "itemImage": None,
        "drugShape": None,
        "colorClass1": None,
        "markCode": None,
        "raw": item,
    }
