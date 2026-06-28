import json
import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

TRANSLATE_SYSTEM_PROMPT = """당신은 다문화 가정 금융교육 서비스의 번역가입니다.

역할: 한국어 대화 스크립트를 외국인 어머니가 이해할 수 있도록 자연스럽게 번역합니다.

제약 조건:
- 반드시 JSON 형식으로만 응답하세요. 다른 텍스트 없이 순수 JSON만 출력하세요.
- 직역하지 말고 자연스러운 구어체로 번역하세요
- 금융 개념은 쉬운 표현으로 번역하세요
- 어머니가 자녀에게 말하는 따뜻한 톤을 유지하세요
- 마지막 질문 형태를 반드시 유지하세요
- 금액은 반드시 원화(원/won) 단위를 유지하세요. đồng, pesos 등 다른 통화로 변환 금지.
- 고유명사(사람 이름)는 번역하지 말고 원문 발음 그대로 사용하세요.
- concept_used는 반드시 입력받은 [연결 금융 개념]의 이름을 그대로 사용하세요. 임의로 만들지 마세요.
- 훈계·강요 표현 금지
  금지: "조심해야 해", "잘 생각해 보자", "~하면 안 돼", "왜 이렇게"
  허용: "어떻게 생각해?", "같이 볼까?", "어땠어?"

출력 형식 (반드시 이 JSON 구조만):
{
  "translated": "번역된 스크립트"
}"""

def fix_currency(text: str) -> str:
    text = re.sub(r'(\d[\d.,]*)\s*(đồng|동)', r'\1 won', text)
    text = re.sub(r'(\d[\d.,]*)\s*(pesos|페소)', r'\1 won', text)
    text = re.sub(r'(\d[\d.,]*)\s*(위안|元|yuan)', r'\1 won', text)
    text = re.sub(r'(\d[\d.,]*)(원)', r'\1 won', text)
    return text

LANGUAGES = {
    "vi": "베트남어",
    "zh": "중국어 (간체)",
    "ph": "필리핀어 (타갈로그어)",
}


def translate_script(script: str, target_lang: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    lang_name = LANGUAGES.get(target_lang, target_lang)

    response = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[
            {"role": "system", "content": TRANSLATE_SYSTEM_PROMPT},
            {"role": "user", "content": f"다음 한국어 스크립트를 {lang_name}로 번역해주세요:\n\n{script}"},
        ],
    )

    raw = response.choices[0].message.content.strip()

    import re
    clean = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
    clean = clean.replace("```json", "").replace("```", "").strip()
    clean = re.sub(r',\s*}', '}', clean)

    parsed = json.loads(clean)
    translated = parsed.get("translated", "")
    return fix_currency(translated)


def run_translation_test():
    # test_results.json에서 생성된 스크립트 불러오기
    with open("test_results.json", "r", encoding="utf-8") as f:
        test_results = json.load(f)

    results = []

    for item in test_results:
        if "error" in item:
            continue

        script = item["result"]["script"]
        case_id = item["id"]
        label = item["label"]

        print(f"\n{'='*60}")
        print(f"[{case_id}] {label}")
        print("=" * 60)
        print(f"\n📝 원문 (한국어):")
        print(f"   {script}")

        translations = {}
        for lang_code, lang_name in LANGUAGES.items():
            translated = translate_script(script, lang_code)
            translations[lang_code] = translated
            print(f"\n🌐 {lang_name}:")
            print(f"   {translated}")

        results.append({
            "id": case_id,
            "label": label,
            "original": script,
            "translations": translations,
        })

    # 결과 저장
    with open("translation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ 번역 완료: translation_results.json 저장됨")


if __name__ == "__main__":
    run_translation_test()