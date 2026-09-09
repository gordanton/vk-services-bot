"""Конфигурация проекта: чтение .env и общие объекты фреймворка."""

import os
from pathlib import Path

from dotenv import load_dotenv
from vkbottle import API
from vkbottle.bot import BotLabeler

from services import services_for_prompt

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        msg = f"В .env не задана переменная {name}. Список переменных смотрите в EnvExample."
        raise RuntimeError(msg)
    return value


VK_TOKEN = _required("VK_TOKEN")
PROXYAPI_KEY = _required("PROXYAPI_KEY")

# Ваш числовой VK id: на него бот присылает заявки и отзывы.
# Если не задан, заявки только пишутся в leads.jsonl.
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

PROXYAPI_BASE_URL = os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/v1")
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-4.1-mini")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "500"))
AI_TIMEOUT = float(os.getenv("AI_TIMEOUT", "60"))
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "10"))

# В Docker пишем заявки в том /app/data, локально — в файл рядом с ботом.
LEADS_FILE = Path(os.getenv("LEADS_FILE", "leads.jsonl"))

AI_SYSTEM_PROMPT = (
    "Ты — ассистент частного специалиста по автоматизации и ИИ. "
    "Он оказывает такие услуги:\n"
    f"{services_for_prompt()}\n\n"
    "Отвечай по-русски, коротко и по делу: не больше трёх-четырёх предложений. "
    "Не используй markdown-разметку, потому что ВКонтакте её не отображает. "
    "Конкретные цены не называй: стоимость зависит от задачи и обсуждается лично. "
    "Если вопрос близок к одной из услуг, коротко объясни, как её можно применить, "
    "и предложи оставить заявку кнопкой в меню. "
    "Если вопрос не про услуги, ответь кратко и верни разговор к делу. "
    "Если не знаешь ответа, честно скажи об этом."
)

MENU_TEXT = (
    "Чем могу помочь? Выберите услугу ниже, чтобы посмотреть, что в неё входит.\n\n"
    "Если кнопок не видно — нажмите значок с квадратиками справа от поля ввода: "
    "ВКонтакте сворачивает клавиатуру и повторное слово «меню» её само не раскроет.\n\n"
    "Можно и просто описать свою задачу словами — отвечу и подскажу вариант решения."
)

ABOUT_TEXT = (
    "Меня зовут Антон. Работаю ведущим специалистом в нефтесервисной компании: "
    "принимаю затраты от субподрядчиков, свожу данные из разных систем и ищу "
    "расхождения по часам.\n\n"
    "Этот опыт перенёс в разработку: делаю чат-ботов и ИИ-ассистентов, "
    "автоматизирую отчётность и сверку данных.\n\n"
    "Инструменты: Python (pandas, openpyxl, aiogram, vkbottle), Power Query, Excel, "
    "Docker, Git. Работаю с GPT, YandexGPT и GigaChat.\n\n"
    "Опишите задачу словами или оставьте заявку — обсудим, что можно сделать."
)

WELCOME_MESSAGE = (
    "{name}, здравствуйте! 👋\n\n"
    "Я бот-помощник. Здесь можно посмотреть услуги, задать вопрос и оставить заявку.\n\n"
    "Выберите пункт меню ниже или просто напишите свою задачу."
)

# Общие объекты фреймворка: API создаётся один раз и переиспользуется,
# лейблер собирает хендлеры из пакета handlers.
api = API(VK_TOKEN)
labeler = BotLabeler()

# Флаги правил считываются в момент регистрации хендлеров, поэтому строка
# должна стоять до импорта пакета handlers. Без неё "Меню" с большой буквы
# (телефоны капитализируют первое слово) не попало бы в текстовое правило.
labeler.vbml_ignore_case = True
