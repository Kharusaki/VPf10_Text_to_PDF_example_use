# app.py

import logging
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_file

from utils.ai_processor import process_dialog_with_ai
from utils.input_loader import load_dialog
from utils.pdf_generator import generate_pdf

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_ROOT / "input"

app = Flask(__name__)
logger = logging.getLogger("flask_app")

# Доступные типы отчётов → имена шаблонов
REPORT_TYPES = {
    "profile": "student_profile_template.html",
    "feedback": "lesson_feedback_template.html",
}

INDEX_HTML = """
<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>AI Client Report Generator</title></head>
<body style="font-family:sans-serif;max-width:640px;margin:40px auto">
  <h1>AI Client Report Generator</h1>
  <form method="POST" action="/generate_form">
    <p><label>Файл диалога из input/:<br>
      <select name="filename">{{ files|join('')|safe }}</select>
    </label></p>
    <p><label>Тип отчёта:<br>
      <select name="report_type">
        <option value="profile">Анкета ученика</option>
        <option value="feedback">Карточка пробного урока</option>
      </select>
    </label></p>
    <p><button type="submit">Сгенерировать PDF</button></p>
  </form>
</body></html>
"""


@app.route("/", methods=["GET"])
def index():
    files = sorted(
        p.name for p in INPUT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".txt", ".json"}
    ) if INPUT_DIR.exists() else []
    options = "".join(f'<option value="{f}">{f}</option>' for f in files)
    return render_template_string(INDEX_HTML, files=[options])


@app.route("/generate", methods=["POST"])
def generate_api():
    """JSON API: {"filename": "...", "report_type": "profile"}"""
    payload = request.get_json(silent=True) or {}
    return _handle_generation(payload)


@app.route("/generate_form", methods=["POST"])
def generate_form():
    """HTML-форма: те же поля, но через form-data."""
    payload = {
        "filename": request.form.get("filename"),
        "report_type": request.form.get("report_type", "profile"),
    }
    return _handle_generation(payload)


def _handle_generation(payload: dict):
    filename = payload.get("filename")
    report_type = payload.get("report_type", "profile")

    if not filename:
        return jsonify({"ok": False, "error": "filename не передан"}), 400
    if report_type not in REPORT_TYPES:
        return jsonify({"ok": False, "error": f"неизвестный report_type: {report_type}"}), 400

    path = INPUT_DIR / filename
    if not path.exists() or not path.is_file():
        return jsonify({"ok": False, "error": f"файл не найден: {filename}"}), 404

    try:
        logger.info("Генерация: %s, тип=%s", filename, report_type)
        dialog_text = load_dialog(path)
        data = process_dialog_with_ai(dialog_text)
        data["source_file"] = path.name
        pdf_path = generate_pdf(data, template_name=REPORT_TYPES[report_type])
        logger.info("Готово: %s", pdf_path.name)
        return jsonify({"ok": True, "pdf_path": str(pdf_path)})
    except Exception as exc:
        logger.error("Ошибка генерации: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    app.run(host="127.0.0.1", port=5000, debug=False)