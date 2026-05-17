import json
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

_SYSTEM_PROMPT = (
    "당신은 시각장애인을 위한 의약품 안내 도우미입니다. "
    "핵심 정보만 쉽고 짧은 문장으로 전달하세요. "
    "의학용어는 반드시 일상어로 바꿔주세요. "
    "실제 의료 진단이나 처방은 절대 하지 마세요. "
    "'도움됩니다', '좋습니다' 같은 광고성 표현은 절대 금지. "
    "약의 실제 적응증을 정확하게 표현하세요 (예: 혈전 억제제입니다, 해열진통제입니다)."
)


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
    """봉지약 음성 스크립트를 Python에서 직접 생성 (AI 없음)"""
    sentences = [f"이 봉지는 {label}입니다"]

    if timing:
        sentences.append(f"{timing}에 복용하는 봉지약입니다")

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
