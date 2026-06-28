import json
from script_generator import generate_script, ScriptGenerationError
from dotenv import load_dotenv

load_dotenv()

TEST_CASES = [
    {
        "id": "CASE-01",
        "label": "간식비 3,000원 증가 (주의)",
        "params": {
            "weekly_data": {
                "total_spent": 19400,
                "budget": 20000,
                "categories": {"snack": 8700, "transport": 5000, "hobby": 5700},
                "prev_week": {"snack": 5700, "transport": 5000, "hobby": 5700},
            },
            "trigger": "snack_increase_30pct",
            "concept_id": "C005",
            "child_name": "민우",
            "child_age": 11,
            "parent_lang": "vi",
        },
    },
    {
        "id": "CASE-02",
        "label": "게임 결제 9,900원 첫 등장 (경고)",
        "params": {
            "weekly_data": {
                "total_spent": 19900,
                "budget": 20000,
                "categories": {"snack": 5000, "game": 9900, "transport": 5000},
                "prev_week": {"snack": 5000, "game": 0, "transport": 5000},
            },
            "trigger": "game_first_appeared",
            "concept_id": "C010",
            "child_name": "민우",
            "child_age": 11,
            "parent_lang": "vi",
        },
    },
    {
        "id": "CASE-03",
        "label": "3주 연속 교통비 일정 (칭찬)",
        "params": {
            "weekly_data": {
                "total_spent": 14000,
                "budget": 20000,
                "categories": {"snack": 4000, "transport": 5000, "hobby": 5000},
                "prev_week": {"snack": 4000, "transport": 5000, "hobby": 5000},
            },
            "trigger": "transport_stable_3weeks",
            "concept_id": "C013",
            "child_name": "민우",
            "child_age": 11,
            "parent_lang": "vi",
        },
    },
    {
        "id": "CASE-04",
        "label": "용돈 92% 소진 (경고)",
        "params": {
            "weekly_data": {
                "total_spent": 18500,
                "budget": 20000,
                "categories": {"snack": 7000, "game": 6500, "transport": 5000},
                "prev_week": {"snack": 5000, "game": 4000, "transport": 5000},
            },
            "trigger": "budget_over_90pct",
            "concept_id": "C008",
            "child_name": "지아",
            "child_age": 11,
            "parent_lang": "zh",
        },
    },
    {
        "id": "CASE-05",
        "label": "3주 연속 저축 0원 (주의)",
        "params": {
            "weekly_data": {
                "total_spent": 19200,
                "budget": 20000,
                "categories": {"snack": 8000, "transport": 5000, "hobby": 6200},
                "prev_week": {"snack": 8000, "transport": 5000, "hobby": 6200},
            },
            "trigger": "no_saving_3weeks",
            "concept_id": "C003",
            "child_name": "소피아",
            "child_age": 9,
            "parent_lang": "ph",
        },
    },
]

PASS_MARK = "\033[92m✓ PASS\033[0m"
FAIL_MARK = "\033[91m✗ FAIL\033[0m"


def run_tests():
    results = []

    for case in TEST_CASES:
        print(f"\n{'='*60}")
        print(f"[{case['id']}] {case['label']}")
        print("=" * 60)

        try:
            result = generate_script(**case["params"])
            print(f"\n📝 생성된 스크립트:")
            print(f"   {result['script']}")
            print(f"\n   개념: {result.get('concept_used')}")
            results.append({"id": case["id"], "label": case["label"], "result": result})

        except ScriptGenerationError as e:
            print(f"\n✗ 생성 실패: {e}")
            results.append({"id": case["id"], "label": case["label"], "error": str(e)})

    print(f"\n{'='*60}")
    print(f"📊 완료: {len([r for r in results if 'result' in r])} / {len(results)} 성공")

    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"결과 저장: test_results.json")


if __name__ == "__main__":
    run_tests()