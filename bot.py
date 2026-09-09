"""Точка входа: ВК-бот на LongPoll API с AI-ответами через ProxyAPI."""

import sys

from vkbottle import Bot
from vkbottle.modules import logger

import ai
import handlers  # noqa: F401  — импорт регистрирует хендлеры в labeler
from config import AI_MODEL, api, labeler

# Консоль Windows по умолчанию в cp1251, а в логи попадают эмодзи из сообщений
# пользователей. Без этого вывод падает с UnicodeEncodeError.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

bot = Bot(api=api, labeler=labeler)

# Правило mention работает только при включённом replace_mention.
bot.labeler.message_view.replace_mention = True

# Корректно закрываем http-сессию клиента ProxyAPI при остановке бота.
bot.on_shutdown.append(ai.close())


if __name__ == "__main__":
    logger.info("Запускаем LongPoll, модель для ответов: {}", AI_MODEL)
    bot.run()
