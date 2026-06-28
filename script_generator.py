import json
import os
from groq import Groq


class ScriptGenerationError(Exception):
    pass


CONCEPT_MAP = {
    "C001": {"name": "지출", "desc": "생활하면서 실제로 돈을 쓰는 것. 카드로 결제하는 모든 것이 지출이에요."},
    "C002": {"name": "예산", "desc": "돈을 쓰기 전에 미리 계획을 세우는 것. 이번 주 어디에 얼마를 쓸지 미리 정해두는 거예요."},
    "C003": {"name": "저축", "desc": "지금 다 쓰지 않고 일부를 남겨두면 나중에 원하는 것을 살 수 있어요."},
    "C005": {"name": "충동소비", "desc": "계획 없이 갑자기 사고 싶어서 쓰는 돈. 편의점에서 배고프지 않은데 과자를 사는 것처럼요."},
    "C006": {"name": "필요 vs 욕구", "desc": "꼭 있어야 하는 것(교통비, 학용품)과 갖고 싶은 것(게임, 간식)의 차이예요."},
    "C008": {"name": "용돈 관리", "desc": "받은 용돈을 미리 계획해서 나눠 쓰는 방법이에요."},
    "C010": {"name": "디지털 소비", "desc": "앱·게임·배달 등 화면 안에서 결제되는 돈. 실물 느낌이 없어서 과소비하기 쉬워요."},
    "C013": {"name": "또래 평균 소비", "desc": "같은 나이 아이들이 보통 얼마를 쓰는지 참고해서 합리적인 기준을 세우는 거예요."},
}

SYSTEM_PROMPT = """당신은 티키(Tiki) 서비스의 대화 스크립트 생성기입니다.

역할: 다문화 가정 외국인 어머니가 자녀와 금융 대화를 나눌 수 있도록 실용적인 대화 스크립트를 생성합니다.

제약 조건:
- 반드시 JSON 형식으로만 응답하세요. 다른 텍스트 없이 순수 JSON만 출력하세요.
- script: 어머니가 오늘 저녁 자녀에게 실제로 말할 수 있는 한국어 문장 2~3개
- 초등 3학년 수준의 쉬운 어휘만 사용하세요
- 잔소리·훈계·강요 표현 금지 (예: "~하면 안 돼", "왜 이렇게", "너무 많이 썼네")
- 반드시 질문으로 끝내세요 (자녀가 대답할 수 있도록)
- 금융 개념을 자연스럽게 녹이되, 용어를 직접 쓰지 마세요
- 입력된 실제 수치(금액, 변화량)만 사용하세요. 수치를 임의로 만들지 마세요.
- concept_used: 사용한 금융 개념명
- "~원밖에 남지 않았어" 같은 잔액 표현 금지. 반드시 "~원을 썼어" 형태로 지출 기준으로 말하세요.
- [한국어 테스트] 반드시 한국어로만 작성하세요. 다른 언어(영어, 중국어, 힌디어 등) 절대 사용 금지.

출력 형식 (반드시 이 JSON 구조만):
{
  "script": "스크립트 문장",
  "concept_used": "개념명",
}"""


def build_user_prompt(weekly_data, trigger, concept, child_name, child_age, parent_lang):
    lang_map = {"vi": "베트남어권", "zh": "중국어권", "ph": "필리핀어권"}
    lang_label = lang_map.get(parent_lang, "베트남어권")

    categories = weekly_data.get("categories", {})
    prev = weekly_data.get("prev_week", {})
    total = weekly_data.get("total_spent", 0)
    budget = weekly_data.get("budget", 0)
    ratio = round(total / budget * 100, 1) if budget else 0

    cat_labels = {"snack": "간식비", "game": "게임 결제", "transport": "교통비", "hobby": "취미/문방구", "etc": "기타"}
    changes = []
    for key, amount in categories.items():
        label = cat_labels.get(key, key)
        prev_amount = prev.get(key, 0)
        diff = amount - prev_amount
        if diff > 0:
            changes.append(f"{label} {amount:,}원 (지난주 대비 +{diff:,}원 증가)")
        elif diff < 0:
            changes.append(f"{label} {amount:,}원 (지난주 대비 {abs(diff):,}원 감소)")
        else:
            changes.append(f"{label} {amount:,}원 (지난주와 동일)")

    changes_text = "\n".join(f"- {c}" for c in changes)

    return f"""[소비 변화 데이터]
자녀 이름: {child_name} ({child_age}세)
이번 주 총 지출: {total:,}원 / 용돈 {budget:,}원 ({ratio}% 소진)
카테고리별:
{changes_text}
트리거 조건: {trigger}

[연결 금융 개념]
{concept['name']} — {concept['desc']}

[부모 프로필]
{lang_label} 어머니
자녀 연령: {child_age}세

위 데이터를 바탕으로 오늘 저녁 어머니가 자녀에게 할 대화 스크립트를 생성해주세요."""


def validate_response(parsed, weekly_data):
    script = parsed.get("script", "")
    checks = {
        "has_question": "?" in script,
        "not_too_long": len(script) <= 200,
        "tone_ok": parsed.get("tone_check") == "잔소리없음",
        "no_hallucination": parsed.get("hallucination_risk", "없음") == "없음",
        "has_concept": bool(parsed.get("concept_used")),
    }

    amounts = [str(v) for v in weekly_data.get("categories", {}).values()]
    amounts += [str(weekly_data.get("total_spent", "")), str(weekly_data.get("budget", ""))]
    checks["uses_real_numbers"] = any(
        a.replace(",", "") in script.replace(",", "") for a in amounts if a
    )

    parsed["quality_checks"] = checks
    parsed["quality_score"] = sum(checks.values())
    parsed["quality_pass"] = parsed["quality_score"] >= 4
    return parsed


def generate_script(weekly_data, trigger, concept_id, child_name="아이", child_age=10, parent_lang="vi"):
    concept = CONCEPT_MAP.get(concept_id)
    if not concept:
        raise ScriptGenerationError(f"알 수 없는 concept_id: {concept_id}")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ScriptGenerationError("GROQ_API_KEY 환경변수가 설정되지 않았습니다.")

    client = Groq(api_key=api_key)
    user_prompt = build_user_prompt(weekly_data, trigger, concept, child_name, child_age, parent_lang)

    response = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()

    try:
        import re
        if '</think>' in raw:
            clean = raw.split('</think>')[-1].strip()
        else:
            clean = re.sub(r'<think>.*', '', raw, flags=re.DOTALL).strip()
    
        clean = clean.replace("```json", "").replace("```", "").strip()
        clean = re.sub(r',\s*}', '}', clean)
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        raise ScriptGenerationError(f"JSON 파싱 실패. 원본 응답: {raw}")

    parsed["concept_id"] = concept_id
    parsed["trigger"] = trigger
    return parsed