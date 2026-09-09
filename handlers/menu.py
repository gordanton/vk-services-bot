"""Главное меню, экраны услуг и раздел «Обо мне»."""

from vkbottle.bot import Message
from vkbottle.modules import logger

from config import ABOUT_TEXT, MENU_TEXT, labeler
from keyboards import MAIN_MENU, service_menu
from services import SERVICES_BY_ID


# Кнопку «Начать» ВКонтакте шлёт как payload {"command": "start"};
# payload_contains переживает лишние поля, text/command ловят набор руками.
@labeler.message(payload={"command": "start"})
@labeler.message(payload_contains={"command": "start"})
@labeler.message(command="start")
@labeler.message(payload={"cmd": "menu"})
@labeler.message(command="меню")
@labeler.message(text=["меню", "начать", "start", "привет"])
async def menu_handler(message: Message) -> None:
    await message.answer(MENU_TEXT, keyboard=MAIN_MENU)


# PayloadMapRule при совпадении возвращает сам payload, поэтому поле sid
# приходит в хендлер обычным аргументом.
@labeler.message(payload_map={"cmd": "service", "sid": str})
async def service_handler(message: Message, sid: str) -> None:
    service = SERVICES_BY_ID.get(sid)
    if service is None:
        logger.warning("Запрошена неизвестная услуга: {}", sid)
        await message.answer("Не нашёл такую услугу, открываю меню.", keyboard=MAIN_MENU)
        return

    logger.info("Диалог {} открыл услугу {}", message.peer_id, sid)
    await message.answer(
        f"{service.title}\n\n{service.description}",
        keyboard=service_menu(service.id),
    )


@labeler.message(payload={"cmd": "about"})
async def about_handler(message: Message) -> None:
    await message.answer(ABOUT_TEXT, keyboard=MAIN_MENU)
