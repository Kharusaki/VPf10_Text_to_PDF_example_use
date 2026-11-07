# utils/ai_processor.py

import json
import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_VALUE = "не указано"


# ============================================================
# Схемы полей для двух типов отчётов
# ============================================================

PROFILE_FIELDS = [
    "student_name",
    "age_or_grade",
    "current_level",
    "learning_goal",
    "preferred_schedule",
    "format_preference",
    "previous_experience",
    "special_notes",
    "contact_info",
    "next_steps",
]

FEEDBACK_FIELDS = [
    "student_name",
    "lesson_date",
    "teacher_name",
    "topic_covered",
    "student_engagement",
    "strengths",
    "areas_to_improve",
    "recommendations",
]


# ============================================================
# Мок-ответы
# ============================================================

def _mock_profile() -> dict:
    return {
        "student_name": "Мария Иванова",
        "age_or_grade": "14 лет, 8 класс",
        "current_level": "B1 (средний)",
        "learning_goal": "Подготовка к ОГЭ по английскому",
        "preferred_schedule": "Вт/Чт после 17:00, Сб утро",
        "format_preference": "Онлайн, мини-группа",
        "previous_experience": "2 года в школьном кружке, репетитора не было",
        "special_notes": "Стесняется говорить вслух, нужен мягкий преподаватель",
        "contact_info": "мама Ольга, +7 999 123-45-67, Telegram @olga_iv",
        "next_steps": "Пробный урок 15 ноября в 18:00, отправить ссылку на оплату",
    }


def _mock_feedback() -> dict:
    return {
        "student_name": "Мария Иванова",
        "lesson_date": "15.11.2025, 18:00",
        "teacher_name": "Анна Петрова",
        "topic_covered": "Present Perfect vs Past Simple, разговорная практика о хобби",
        "student_engagement": "Активно, но стеснялась в начале, к концу разговорилась",
        "strengths": "Хороший словарный запас, понимает грамматику на слух",
        "areas_to_improve": "Беглость речи, уверенность при монологе",
        "recommendations": "Записать в мини-группу B1, 2 раза в неделю, акцент на speaking",
    }


# ============================================================
# Промпты
# ============================================================

def _build_prompt(dialog_text: str, field_keys: list[str], role_context: str) -> str:
    fields_description = "\n".join(f'- "{k}"' for k in field_keys)
    return f"""Ты — ассистент школы английского языка. {role_context}

Твоя задача: извлечь данные и вернуть СТРОГО JSON без markdown-обёрток,
без пояснений, без текста до или после JSON.

Схема JSON (все значения — строки):
{fields_description}

Правила:
1. Если информации по полю в диалоге нет — поставь строку "{DEFAULT_VALUE}".
2. Не выдумывай факты, которых нет в диалоге.
3. Формат входа может быть разным: чистый текст, реплики с ролями
   ("Менеджер:", "Клиент:"), markdown, JSON с историей сообщений.
   Во всех случаях интерпретируй содержимое как диалог.
4. Отвечай только JSON-объектом.

Транскрибация:
---
{dialog_text}
---
"""


PROFILE_CONTEXT = (
    "На вход получаешь транскрибацию диалога менеджера с потенциальным учеником "
    "(или его родителем). Извлеки данные для анкеты ученика."
)

FEEDBACK_CONTEXT = (
    "На вход получаешь транскрибацию или заметки по итогам пробного урока. "
    "Извлеки данные для карточки пробного урока."
)


# ============================================================
# Общий вызов ИИ
# ============================================================

def _call_ai(prompt: str, mock_data: dict, field_keys: list[str]) -> dict:
    """
    Отправляет промпт в OpenAI, парсит JSON, нормализует поля.
    При любой ошибке (или в мок-режиме) возвращает mock_data.
    """
    use_mock = os.getenv("USE_MOCK_AI", "true").lower() == "true"
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if use_mock or not api_key:
        logger.info("USE_MOCK_AI=true или ключ не задан — возвращаю мок-ответ.")
        return dict(mock_data)

    try:
        logger.info("Отправляю запрос в OpenAI (длина промпта: %d символов).", len(prompt))
        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/v1"),
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        logger.info("Ответ OpenAI получен (%d символов).", len(raw))

        data = _parse_json_safely(raw)
        data = _normalize_fields(data, field_keys)
        logger.info("JSON успешно разобран и провалидирован.")
        return data

    except Exception as exc:
        logger.error("Ошибка при работе с OpenAI: %s. Возвращаю мок.", exc)
        return dict(mock_data)


# ============================================================
# Публичные функции — по одной на тип отчёта
# ============================================================

def process_dialog_with_ai(dialog_text: str) -> dict:
    """Анкета ученика (первичный диалог)."""
    if not dialog_text or not dialog_text.strip():
        logger.warning("Пустой текст диалога — возвращаю мок профиля.")
        return _mock_profile()
    prompt = _build_prompt(dialog_text, PROFILE_FIELDS, PROFILE_CONTEXT)
    return _call_ai(prompt, _mock_profile(), PROFILE_FIELDS)


def process_lesson_feedback_with_ai(dialog_text: str) -> dict:
    """Карточка пробного урока (по итогам занятия)."""
    if not dialog_text or not dialog_text.strip():
        logger.warning("Пустой текст диалога — возвращаю мок feedback.")
        return _mock_feedback()
    prompt = _build_prompt(dialog_text, FEEDBACK_FIELDS, FEEDBACK_CONTEXT)
    return _call_ai(prompt, _mock_feedback(), FEEDBACK_FIELDS)


# ============================================================
# Вспомогательные (без изменений по сути)
# ============================================================

def _parse_json_safely(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


def _normalize_fields(data: dict, field_keys: list[str]) -> dict:
    result = {}
    for key in field_keys:
        value = data.get(key, DEFAULT_VALUE)
        if value is None or (isinstance(value, str) and not value.strip()):
            value = DEFAULT_VALUE
        result[key] = str(value).strip()
    return result