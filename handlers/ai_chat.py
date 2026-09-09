"""Ответы на свободный текст через AI."""

from vkbottle import VKAPIError
from vkbottle.bot import Message
from vkbottle.modules import logger

from ai import AIError, ask, reset_history
from config import labeler
from keyboards import MAIN_MENU


async def _show_typing(message: Message) -> None:
    """Показывает "печатает…", пока модель формирует ответ."""
    try:
        await message.ctx_api.messages.set_activity(peer_id=message.peer_id, type="typing")
    except VKAPIError as e:
        logger.debug("Не удалось показать индикатор набора: {}", e.error_msg)


@labeler.message(command="сброс")
async def reset_handler(message: Message) -> None:
    reset_history(message.peer_id)
    await message.answer(
        "Контекст диалога очищен, начнём с чистого листа.",
        keyboard=MAIN_MENU,
    )


# Хендлер без правил ловит всё остальное, поэтому регистрируется последним:
# хендлеры блокирующие, и до следующих дело уже не дойдёт.
@labeler.message()
async def ai_handler(message: Message) -> None:
    question = (message.text or "").strip()
    if not question:
        await message.answer(
            "Я понимаю только текст — опишите задачу словами или выберите пункт меню.",
            keyboard=MAIN_MENU,
        )
        return

    logger.info("Вопрос из диалога {}: {}", message.peer_id, question)
    await _show_typing(message)

    try:
        answer = await ask(message.peer_id, question)
    except AIError:
        await message.answer(
            "Не получилось получить ответ от ИИ. Попробуйте, пожалуйста, ещё раз чуть позже "
            "или выберите услугу в меню.",
            keyboard=MAIN_MENU,
        )
        return

    logger.info("Ответ ИИ для диалога {}: {}", message.peer_id, answer)
    await message.answer(answer, keyboard=MAIN_MENU)
