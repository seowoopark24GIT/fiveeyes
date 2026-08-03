import json
import re
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

_IDENTIFY_SYSTEM = (
    "당신은 시각장애인을 위한 제품 식별 도우미입니다. "
    "사진 속 포장·라벨·알약·튜브 등을 보고 의약품(medicine)인지 화장품(cosmetic)인지 분류합니다. "
    "제품명을 한글로 최대한 정확히 추정하고, 촉각·형태 중심으로 짧게 설명합니다. "
    "화장품인 경우에만 브랜드/제품 용도에 대해 알고 있는 일반 지식을 추가로 짧게 답하세요 "
    "(공식 확인이 아닌 참고용임을 스스로 인지하고 답할 것). "
    "의약품인 경우 이 필드는 비워두세요 — 의약품 효능·용법은 반드시 공식 데이터로만 안내합니다. "
    "의료 진단·처방은 하지 마세요. JSON만 출력하세요."
)

_SYSTEM_PROMPT = (
    "당신은 시각장애인을 위한 의약품 안내 도우미입니다. "
    "핵심 정보만 쉽고 짧은 문장으로 전달하세요. "
    "의학용어는 반드시 일상어로 바꿔주세요. "
    "실제 의료 진단이나 처방은 절대 하지 마세요. "
    "'도움됩니다', '좋습니다' 같은 광고성 표현은 절대 금지. "
    "약의 실제 적응증을 정확하게 표현하세요 (예: 혈전 억제제입니다, 해열진통제입니다)."
)


async def identify_from_image(image_base64: str) -> dict:
    """GPT Vision으로 약품/화장품 분류 및 이름·형태 추정"""
    image_url = image_base64
    if image_base64 and not image_base64.startswith("data:"):
        image_url = f"data:image/jpeg;base64,{image_base64}"

    response = await _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _IDENTIFY_SYSTEM},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "사진 속 제품을 분석해 JSON으로 답하세요.\n"
                            '{ "product_type": "medicine"|"cosmetic"|"unknown", '
                            '"name_guess": "추정 제품명", '
                            '"short_label": "점자·음성용 10자 이내 짧은 이름", '
                            '"visual_description": "촉각·형태 중심 25자 이내 설명", '
                            '"ai_guess_info": "화장품일 때만: 브랜드/용도/색상에 대해 아는 내용 30자 이내, 의약품이면 빈 문자열", '
                            '"confidence": "high"|"medium"|"low" }'
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=300,
    )

    result = json.loads(response.choices[0].message.content)
    product_type = result.get("product_type", "unknown")
    if product_type not in {"medicine", "cosmetic", "unknown"}:
        product_type = "unknown"
    return {
        "product_type": product_type,
        "name_guess": (result.get("name_guess") or "").strip(),
        "short_label": (result.get("short_label") or result.get("name_guess") or "").strip(),
        "visual_description": (result.get("visual_description") or "").strip(),
        "ai_guess_info": (result.get("ai_guess_info") or "").strip() if product_type == "cosmetic" else "",
        "confidence": result.get("confidence", "medium"),
    }


def build_identification_voice(
    product_type: str,
    item_name: str,
    summary_lines: list[str],
    verified: bool,
    ai_guess_info: str | None = None,
) -> list[str]:
    """촬영 후 확인용 음성 스크립트 (TTS 재생 순서)"""
    kind = "의약품" if product_type == "medicine" else "화장품"
    sentences = [f"촬영하신 것은 {item_name} {kind}으로 확인됩니다."]
    sentences.extend(line for line in summary_lines if line)

    if not verified:
        sentences.append("공식 데이터베이스에서 일치하는 정보를 찾지 못했습니다.")
        # 화장품에 한해서만 AI 추정 정보를 참고용으로 안내 (의약품은 공식 데이터 없이는 정보 제공 금지)
        if product_type == "cosmetic" and ai_guess_info:
            sentences.append("아래는 공식 확인이 안 된, AI가 추정한 참고 정보입니다.")
            sentences.append(ai_guess_info)

    sentences.append(
        "맞으면 '맞아'라고, 틀리면 '다시'라고 말씀해 주세요. "
        "또는 화면의 버튼을 눌러 주세요."
    )
    return sentences


def _trim_sentence(text: str, max_len: int = 25) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text).replace("\n", " ").strip()
    clean = re.sub(r"\s+", " ", clean)
    if len(clean) <= max_len:
        return clean
    dot = clean.find(".")
    if 0 < dot < max_len:
        return clean[: dot + 1]
    return clean[:max_len]


async def analyze_cosmetic(cosmetic_info: dict, short_name: str | None = None) -> list[str]:
    """화장품 공식 데이터 기반 음성 안내 스크립트"""
    display_name = short_name or cosmetic_info.get("itemName", "")
    prompt_text = f"""다음 화장품 정보를 바탕으로 시각장애인 음성 안내 문장을 JSON으로 만들어주세요.

제품명: {cosmetic_info.get('itemName', '')}
제조사: {cosmetic_info.get('manufacturer', '')}
주의사항: {cosmetic_info.get('atpnWarnQesitm', '')}

아래 항목을 JSON 배열 voice_script로 작성:
A (필수): 제품 용도 — 20자 이내
B (필수): 가장 중요한 주의사항 — 20자 이내
C (선택): 사용 팁 — 20자 이내

규칙: 각 문장 최대 25자. JSON만 출력."""

    response = await _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "시각장애인을 위한 화장품 안내 도우미입니다. 짧고 쉬운 문장만 사용하세요.",
            },
            {"role": "user", "content": prompt_text},
        ],
        response_format={"type": "json_object"},
        max_tokens=300,
    )
    result = json.loads(response.choices[0].message.content)
    cleaned = [_trim_sentence(s) for s in result.get("voice_script", []) if s]
    return [f"이 제품은 {display_name}입니다"] + cleaned


async def analyze_drug(drug_info: dict, image_url: str | None = None, short_name: str | None = None) -> list[str]:
    """식약처 데이터를 분석해 음성 안내 스크립트(문장 리스트) 반환"""

    display_name = short_name or drug_info.get('itemName', '')

    prompt_text = f"""다음 의약품 정보를 바탕으로 시각장애인 음성 안내 문장을 JSON으로 만들어주세요.

전체 약 이름: {drug_info.get('itemName', '')}
효능: {drug_info.get('efcyQesitm', '')}
복용방법: {drug_info.get('useMethodQesitm', '')}
주의사항: {drug_info.get('atpnWarnQesitm', '')}
부작용: {drug_info.get('seQesitm', '')}

아래 항목을 순서대로 JSON 배열로 작성하세요:

A (필수): 이 약의 핵심 기전/용도 — 20자 이내로 단 하나만
   올바른 예: "혈전 생성을 억제하는 약입니다", "해열·진통에 쓰는 약입니다", "혈압을 낮추는 약입니다", "콜레스테롤을 낮추는 약입니다"
   금지: 원문 나열 복사("심근경색, 뇌경색, 불안정형 협심증..." 식의 나열), 색상/형태 설명, "도움됩니다", "좋습니다"
   핵심: 핵심 기전 하나만 ("혈전 억제", "해열진통", "혈압강하" 등)
B (필수): 가장 중요한 주의사항 — 20자 이내
C (선택): 두 번째 주의사항 (없으면 생략) — 20자 이내
D (필수): 복용방법 — 20자 이내
E (선택): 알약 형태 — 색상 언급 금지, 촉각으로 구분할 수 있는 모양/크기/각인만
   올바른 예: "길쭉한 캡슐 형태입니다", "작고 둥근 알약입니다", "표면에 선이 있는 타원형입니다"
   금지: 흰색, 주황색, 노란색 등 색상

{{
  "voice_script": ["A 문장", "B 문장", "C 문장(선택)", "D 문장", "E 문장(선택)"]
}}

규칙: 각 문장 최대 25자. 원문 복사 절대 금지. JSON만 출력."""

    content: list[dict] = [{"type": "text", "text": prompt_text}]

    if image_url:
        content.insert(1, {"type": "image_url", "image_url": {"url": image_url}})

    response = await _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        response_format={"type": "json_object"},
        max_tokens=500,
    )

    result = json.loads(response.choices[0].message.content)
    gpt_sentences = result.get("voice_script", [])

    # GPT가 너무 긴 문장을 생성하면 첫 마침표까지만 사용
    cleaned = []
    for s in gpt_sentences:
        if len(s) > 30:
            dot = s.find('.')
            s = s[:dot + 1] if 0 < dot < 30 else s[:30]
        cleaned.append(s)

    # 약 이름 문장은 Python에서 직접 생성 (GPT가 임의로 바꾸지 못하게)
    return [f"이 약은 {display_name}입니다"] + cleaned


def build_packet_voice_script(
    label: str,
    purpose: str,
    timing: str | None,
    drugs: list[dict],
    extra_caution: str | None,
) -> list[str]:
    """묶음 제품 음성 스크립트를 Python에서 직접 생성 (AI 없음)"""
    sentences = [f"이 묶음은 {label}입니다"]

    if timing:
        sentences.append(f"{timing}에 복용하는 묶음 제품입니다")

    sentences.append(purpose)

    for drug in drugs:
        line = f"{drug['name']} {drug['count']}정"
        efficacy = drug.get("efficacy") or ""
        if efficacy:
            # 안전망: 30자 초과 시 첫 마침표까지, 없으면 30자로 절단
            dot = efficacy.find(".")
            efficacy = efficacy[:dot + 1] if 0 < dot < 30 else efficacy[:30]
            line += f" — {efficacy}"
        sentences.append(line)

    # 주의사항: 각 약에서 수집 후 첫 번째만 사용 (중복 방지)
    cautions = [d["caution"] for d in drugs if d.get("caution")]
    if extra_caution:
        cautions.append(extra_caution)
    if cautions:
        sentences.append(cautions[0])

    return sentences
