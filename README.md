# AI Client Report Generator

Автоматическая генерация PDF-отчётов по диалогам с клиентами школы английского языка.
Пайплайн: транскрибация диалога → ИИ извлекает структурированные данные (JSON) →
HTML-шаблон (Jinja2) → PDF (WeasyPrint) → `reports/`.

## Что умеет

- Принимает транскрибацию в двух форматах: **чистый `.txt`** и **JSON с историей сообщений** (как отдаёт Telegram/VK-бот).
- Извлекает данные через OpenAI (поддерживается ProxyAPI через `OPENAI_BASE_URL`).
- Генерирует **два типа отчётов**:
  - `profile` — анкета ученика (10 полей, для личного дела);
  - `feedback` — карточка пробного урока (8 полей, по итогам занятия).
- Сохраняет PDF в `reports/` с уникальным именем (тип отчёта + источник + timestamp).
- Логирует все этапы в консоль и `app.log`.
- При ошибке ИИ (сеть, ключ, формат) — не падает, а отдаёт мок-ответ, чтобы пайплайн завершился.
- Есть локальный Flask-сервер для генерации через форму/API.

## Структура проекта
.
├── main.py # CLI: запуск пайплайна
├── app.py # Flask-сервер (локальный)
├── templates/
│ ├── student_profile_template.html
│ └── lesson_feedback_template.html
├── reports/ # сюда сохраняются PDF
├── input/ # сюда кладутся txt/json с диалогами
├── utils/
│ ├── init.py
│ ├── ai_processor.py # вызов OpenAI, парсинг JSON, мок
│ ├── input_loader.py # чтение txt/json → единый текст диалога
│ └── pdf_generator.py # Jinja2 + WeasyPrint
├── .env.example
├── requirements.txt
└── README.md

## Установка

### 1. Системные зависимости (Windows)

WeasyPrint на Windows требует GTK3 Runtime:
1. Скачать установщик: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
2. Установить (галочка «Add to PATH» включена).
3. Перезагрузить терминал (иногда — компьютер).
4. Проверить: `python -m weasyprint --info` — не должно падать.

### 2. Python-зависимости

```bash
pip install -r requirements.txt

###3. Настройка .env
Скопировать .env.example → .env и заполнить:

text
OPENAI_API_KEY=ваш_ключ
OPENAI_BASE_URL=https://api.proxyapi.ru/v1
USE_MOCK_AI=false

### Запуск (CLI)
bash
# все файлы из input/, тип отчёта по умолчанию — анкета
python main.py

# один конкретный файл
python main.py input/dialog_clean.txt

# конкретный тип отчёта
python main.py --report feedback

# оба типа отчёта для всех файлов (2 файла × 2 типа = 4 PDF)
python main.py --report all
PDF появятся в reports/ с именами вида:
student_profile_dialog_clean_txt_2025-11-13_02-30-15.pdf

### Запуск (Flask)
bash
python app.py
Открыть http://127.0.0.1:5000 — форма: выбрать файл из input/, выбрать тип отчёта,
нажать «Сгенерировать PDF». API: POST /generate с JSON
{"filename": "dialog_clean.txt", "report_type": "profile"}.

### Форматы входных данных
1. Чистый текст (input/dialog_clean.txt):

text
Менеджер: Здравствуйте! ...
Клиент: Хочу записать дочку ...
2. JSON с историей сообщений (input/dialog_bot.json):

json
{
  "chat_id": 84219,
  "messages": [
    {"from": "bot", "text": "..."},
    {"from": "user", "text": "..."}
  ]
}
input_loader.py приводит оба формата к единому виду «Роль: реплика» перед отправкой в ИИ.

## Обработка ошибок
- Ошибка OpenAI (сеть, ключ, формат JSON) → лог `ERROR` + fallback на мок-ответ, пайплайн завершается успешно.
- Пустой файл → пропускается с предупреждением, остальные обрабатываются.
- Ошибка на одном файле → логируется, цикл продолжается со следующим.

## Ограничения учебного проекта
- Шаблоны намеренно без дизайна (белый лист + таблица) — фокус на пайплайне, не на вёрстке.
- Flask-сервер локальный (127.0.0.1), без авторизации — не предназначен для публичного размещения.
- Мок-ответы статичны и не зависят от входного текста (по дизайну, для демо без ИИ).