import re
import difflib
import httpx
from config import MFDS_API_KEY

_BASE = "https://apis.data.go.kr/1471000"

# 공공데이터포털에서 발급받은 서비스 기준:
# - MdcinGrnIdntfcInfoService03 : 낱알 식별 정보 (이미지, 모양, 색상)
# - DrbEasyDrugInfoService       : 쉬운 의약품 정보 (효능, 복용법, 주의사항)

_CHILD_KEYWORDS = ("어린이", "소아")


def _extract_digits(text: str) -> str:
    return "".join(re.findall(r"\d+", text or ""))


def _score_match(query: str, candidate_name: str) -> float:
    """query(원본 추정명)와 candidate_name(API 결과)의 유사도 점수.
    같은 브랜드라도 용량이 다르거나 소아용/성인용이 뒤바뀐 항목을 걸러내기 위함.
    (예: "타이레놀500mg" 조회 시 "어린이타이레놀산160밀리그램"이 뽑히는 것 방지)
    """
    score = difflib.SequenceMatcher(None, query, candidate_name).ratio()

    q_digits = _extract_digits(query)
    c_digits = _extract_digits(candidate_name)
    if q_digits and c_digits:
        score += 0.5 if q_digits == c_digits else -0.3

    q_child = any(kw in query for kw in _CHILD_KEYWORDS)
    c_child = any(kw in candidate_name for kw in _CHILD_KEYWORDS)
    if q_child != c_child:
        score -= 0.4

    return score


def _pick_best_match(query: str, items: list[dict]) -> dict:
    if len(items) == 1:
        return items[0]
    return max(items, key=lambda item: _score_match(query, item.get("itemName") or ""))


async def search_drug_info(item_name: str) -> list[dict]:
    """식약처 쉬운 의약품 정보 조회 (효능/복용법/주의사항/부작용)"""
    url = f"{_BASE}/DrbEasyDrugInfoService/getDrbEasyDrugList"
    params = {
        "serviceKey": MFDS_API_KEY,
        "itemName": item_name,
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


async def search_drug_appearance(item_name: str) -> dict | None:
    """식약처 낱알 식별 정보 조회 (이미지 URL, 모양, 색상, 각인)
    사용자 등록 서비스: MdcinGrnIdntfcInfoService03
    """
    url = f"{_BASE}/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03"
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
        return None

    items = items if isinstance(items, list) else [items]
    item = _pick_best_match(item_name, [{**i, "itemName": i.get("ITEM_NAME")} for i in items])
    return {
        "itemSeq":    item.get("ITEM_SEQ"),
        "itemImage":  item.get("ITEM_IMAGE"),
        "drugShape":  item.get("DRUG_SHAPE"),
        "colorClass1": item.get("COLOR_CLASS1"),
        "colorClass2": item.get("COLOR_CLASS2"),
        "markCode":   item.get("MARK_CODE_FRONT_ANAL") or item.get("MARK_CODE_BACK_ANAL"),
        "lengLong":   item.get("LENG_LONG"),
        "lengShort":  item.get("LENG_SHORT"),
    }


# 약형 접미사 패턴: 정/캡슐/서방정 등
_SUFFIX_RE = re.compile(
    r'(서방형|장용성|필름코팅|연질|겔|서방|장용)?(정|캡슐|정제|환|산|과립|시럽|액|주|앰플|크림|연고|패치|포)\s*$'
)


async def search_drug_info_smart(item_name: str) -> list[dict]:
    """단계적 폴백 검색: 전체 이름 → 숫자 전까지 → 약형 접미사 제거 → 괄호 안 성분명"""
    candidates: list[str] = [item_name]

    # 용량 숫자 이전까지 (예: "아스피린100mg정" → "아스피린")
    before_digits = re.split(r'\d', item_name)[0].strip()
    if before_digits and before_digits != item_name:
        candidates.append(before_digits)

    # 약형 접미사 제거 (예: "아모잘탄정" → "아모잘탄")
    no_suffix = _SUFFIX_RE.sub('', item_name).strip()
    if no_suffix and no_suffix not in candidates:
        candidates.append(no_suffix)

    # 괄호 안 성분명 (예: "타이레놀(아세트아미노펜)" → "아세트아미노펜")
    m = re.search(r'\(([^)]+)\)', item_name)
    if m:
        generic = m.group(1).strip()
        if generic not in candidates:
            candidates.append(generic)

    for name in candidates:
        if len(name) < 2:
            continue
        result = await search_drug_info(name)
        if result:
            best = _pick_best_match(item_name, result)
            return [best] + [d for d in result if d is not best]

    return []


async def get_drug_by_item_seq(item_seq: str) -> dict | None:
    """품목일련번호로 쉬운 의약품 정보 직접 조회 (NFC 탭 시 사용)"""
    url = f"{_BASE}/DrbEasyDrugInfoService/getDrbEasyDrugList"
    params = {
        "serviceKey": MFDS_API_KEY,
        "itemSeq": item_seq,
        "type": "json",
        "numOfRows": 1,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    body = data.get("body", {})
    items = body.get("items", [])
    if not items:
        return None
    return items[0] if isinstance(items, list) else items
