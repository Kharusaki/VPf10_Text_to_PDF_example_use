# utils/input_loader.py

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_dialog(path: Path) -> str:
    """
    Читает файл и возвращает текст диалога в едином формате
    'Роль: реплика' — независимо от исходного формата (txt или json).
    """
    raw = path.read_text(encoding="utf-8")

    # Пробуем распарсить как JSON — если получилось, конвертируем в текст
    if path.suffix.lower() == ".json" or _looks_like_json(raw):
        try:
            data = json.loads(raw)
            return _json_to_dialog_text(data)
        except json.JSONDecodeError:
            logger.warning("%s похож на JSON, но не парсится. Читаю как обычный текст.", path.name)

    return raw


def _looks_like_json(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[")


def _json_to_dialog_text(data: dict) -> str:
    """Превращает JSON с messages в 'Роль: реплика'."""
    messages = data.get("messages", [])
    if not messages:
        # На случай, если JSON другой структуры — вернём как есть
        return json.dumps(data, ensure_ascii=False, indent=2)

    lines = []
    for msg in messages:
        role = msg.get("from", "unknown")
        # Приводим роли к человекочитаемым
        role_ru = {"bot": "Менеджер", "user": "Клиент"}.get(role, role)
        text = msg.get("text", "").strip()
        if text:
            lines.append(f"{role_ru}: {text}")
    return "\n".join(lines)