# utils/pdf_generator.py

import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

logger = logging.getLogger(__name__)

# Пути считаем от корня проекта (файл лежит в utils/, значит корень — parent.parent)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"


def generate_pdf(
    report_data: dict,
    template_name: str = "student_profile_template.html",
    filename_prefix: str = "student_profile",
) -> Path:
    """
    Принимает dict с данными, генерирует PDF в reports/.
    filename_prefix задаёт начало имени файла (тип отчёта).
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Загружаю шаблон: %s", template_name)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)

    context = {
        **report_data,
        "report_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "source_file": report_data.get("source_file", "—"),
    }

    html_string = template.render(**context)
    logger.info("HTML отрендерен (%d символов).", len(html_string))

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    source = report_data.get("source_file", "manual")
    safe_source = "".join(c for c in source if c.isalnum() or c in "_-")[:40]
    output_path = REPORTS_DIR / f"{filename_prefix}_{safe_source}_{timestamp}.pdf"

    logger.info("Генерирую PDF: %s", output_path.name)
    HTML(string=html_string).write_pdf(str(output_path))
    logger.info("PDF сохранён: %s", output_path)

    return output_path

    # 1. Загружаем шаблон
    logger.info("Загружаю шаблон: %s", template_name)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)

    # 2. Добавляем метаданные, которых нет в ответе ИИ
    context = {
        **report_data,
        "report_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "source_file": report_data.get("source_file", "—"),
    }

    # 3. Рендерим HTML
    html_string = template.render(**context)
    logger.info("HTML отрендерен (%d символов).", len(html_string))

    # 4. Имя файла с timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # sanitize: имя входного файла без расширений, только буквы/цифры/_
    source = report_data.get("source_file", "manual")
    safe_source = "".join(c for c in source if c.isalnum() or c in "_-")[:40]
    output_path = REPORTS_DIR / f"student_profile_{safe_source}_{timestamp}.pdf"

    # 5. HTML → PDF
    logger.info("Генерирую PDF: %s", output_path.name)
    HTML(string=html_string).write_pdf(str(output_path))
    logger.info("PDF сохранён: %s", output_path)

    return output_path