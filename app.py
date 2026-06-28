from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from script_generator import generate_script, ScriptGenerationError
import os

load_dotenv()

app = Flask(__name__)
CORS(app)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "tiki-script-api"})


@app.route("/api/script/generate", methods=["POST"])
def generate():
    data = request.get_json()

    if not data:
        return jsonify({"error": "요청 데이터가 없습니다."}), 400

    required = ["weekly_data", "trigger", "concept_id"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"필수 필드 누락: {', '.join(missing)}"}), 400

    try:
        result = generate_script(
            weekly_data=data["weekly_data"],
            trigger=data["trigger"],
            concept_id=data["concept_id"],
            child_name=data.get("child_name", "아이"),
            child_age=data.get("child_age", 10),
            parent_lang=data.get("parent_lang", "vi"),
        )
        return jsonify({"success": True, "data": result})

    except ScriptGenerationError as e:
        return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        return jsonify({"success": False, "error": "서버 오류가 발생했습니다."}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)