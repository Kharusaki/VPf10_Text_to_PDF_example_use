# main.py

import argparse
import logging
import sys
from pathlib import Path

from utils.ai_processor import (
    process_dialog_with_ai,
    process_lesson_feedback_with_ai,
)
from utils.input_loader import load_dialog
from utils.pdf_generator import generate_pdf

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_ROOT / "input"
LOG_FILE = PROJECT_ROOT / "app.log"

# Переключатель типов отчётов — единое место
REPORT_TYPES = {
    "profile": {
        "template": "student_profile_template.html",
        "processor": process_dialog_with_ai,
        "prefix": "student_profile",
    },
    "feedback": {
        "template": "lesson_feedback_template.html",
        "processor": process_lesson_feedback_with_ai,
        "prefix": "lesson_feedback",
    },
}


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def process_file(path: Path, report_type: str) -> Path | None:
    logger = logging.getLogger("main")
    config = REPORT_TYPES[report_type]
    try:
        logger.info("Читаю файл: %s (тип отчёта: %s)", path.name, report_type)
        dialog_text = load_dialog(path)
        if not dialog_text.strip():
            logger.warning("Файл пуст, пропускаю: %s", path.name)
            return None

        data = config["processor"](dialog_text)
        data["source_file"] = path.name

        pdf_path = generate_pdf(
            data,
            template_name=config["template"],
            filename_prefix=config["prefix"],
        )
        print(f"Отчёт успешно создан: {pdf_path}")
        return pdf_path

    except Exception as exc:
        logger.error("Ошибка при обработке %s: %s", path.name, exc)
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Client Report Generator")
    parser.add_argument(
        "file",
        nargs="?",
        help="Путь к одному файлу (если не указан — все из input/)",
    )
    parser.add_argument(
        "--report",
        choices=["profile", "feedback", "all"],
        default="profile",
        help="Тип отчёта: profile (по умолчанию), feedback, all (оба)",
    )
    return parser.parse_args()


def main() -> None:
    setup_logging()
    logger = logging.getLogger("main")
    args = parse_args()

    if args.file:
        target = Path(args.file)
        if not target.is_absolute():
            target = PROJECT_ROOT / target
        if not target.exists():
            logger.error("Файл не найден: %s", target)
            sys.exit(1)
        files = [target]
    else:
        if not INPUT_DIR.exists():
            logger.error("Папка input/ не найдена: %s", INPUT_DIR)
            sys.exit(1)
        files = sorted(
            list(INPUT_DIR.glob("*.txt")) + list(INPUT_DIR.glob("*.json"))
        )
        if not files:
            logger.warning("В папке input/ нет .txt или .json файлов.")
            return

    report_types = list(REPORT_TYPES.keys()) if args.report == "all" else [args.report]

    logger.info("Файлов: %d, типов отчётов: %d", len(files), len(report_types))

    success, failed = 0, 0
    for path in files:
        for report_type in report_types:
            if process_file(path, report_type):
                success += 1
            else:
                failed += 1

    logger.info("Готово. Успешно: %d, с ошибкой: %d", success, failed)


if __name__ == "__main__":
    main()