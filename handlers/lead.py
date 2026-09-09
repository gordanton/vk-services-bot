"""Сбор заявок и отзывов пошагово, через WaiterMachine."""

import datetime as dt
import json

from vkbottle import VKAPIError
from vkbottle.bot import Message
from vkbottle.dispatch.handlers.from_func_handler import FromFuncHandler
from vkbottle.dispatch.rules.base import FuncRule
from vkbottle.modules import logger
from vkbottle.tools import WaiterMachine

from config import ADMIN_ID, LEADS_FILE, labeler
from keyboards import MAIN_MENU
from services import SERVICES_BY_ID

wm = WaiterMachine()
CANCEL_WORDS = {"отмена", "отменить", "стоп", "назад", "меню"}

# Если пользователь бросил заполнение, ожидание снимается при его следующем
# сообщении, и оно обрабатывается обычными хендлерами.
STEP_TIMEOUT = dt.timedelta(minutes=15)


def _is_cancel(text: str) -> bool:
    return text.strip().lower().lstrip("/") in CANCEL_WORDS


def _looks_like_contact(message: Message) -> bool:
    """Контакт принимаем, если в тексте есть цифры или собака. Отмену пропускаем всегда."""
    text = (message.text or "").strip()
    if _is_cancel(text):
        return True
    return len(text) >= 5 and (any(char.isdigit() for char in text) or "@" in text)


async def _ask_contact_again(message: Message) -> None:
    await message.answer(
        "Это не похоже на контакт. Напишите телефон, ник в Telegram или e-mail.\n"
        "Либо «отмена», чтобы прервать."
    )


# default принимает обработчик, а не строку: при непрохождении правила он
# отправляет подсказку, а ожидание остаётся активным.
_CONTACT_RETRY = FromFuncHandler(_ask_contact_again)


def _save(record: dict) -> None:
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LEADS_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


async def _notify_admin(message: Message, text: str) -> None:
    if not ADMIN_ID:
        logger.warning("ADMIN_ID не задан — запись сохранена только в {}", LEADS_FILE)
        return
    try:
        await message.ctx_api.messages.send(peer_id=ADMIN_ID, message=text, random_id=0)
    except VKAPIError as e:
        logger.error("Не удалось отправить уведомление админу: {}", e.error_msg)


@labeler.message(payload_map={"cmd": "lead", "sid": str})
async def lead_handler(message: Message, sid: str) -> None:
    service = SERVICES_BY_ID.get(sid)
    title = service.title if service else "Услуга не выбрана"

    await message.answer(
        f"Оформляем заявку: {title}.\n\n"
        "Опишите задачу одним сообщением: что нужно сделать и к какому сроку.\n"
        "Чтобы прервать, напишите «отмена»."
    )

    task_message, _ = await wm.wait(labeler.message_view, message, expiration=STEP_TIMEOUT)
    task = (task_message.text or "").strip()
    if _is_cancel(task):
        await message.answer("Заявка отменена.", keyboard=MAIN_MENU)
        return

    await message.answer(
        "Принял. Оставьте контакт для связи: телефон, ник в Telegram или e-mail."
    )
    contact_message, _ = await wm.wait(
        labeler.message_view,
        message,
        FuncRule(_looks_like_contact),
        default=_CONTACT_RETRY,
        expiration=STEP_TIMEOUT,
    )
    contact = (contact_message.text or "").strip()
    if _is_cancel(contact):
        await message.answer("Заявка отменена.", keyboard=MAIN_MENU)
        return

    users_info = await message.ctx_api.users.get(user_ids=[message.from_id])
    user = users_info[0]
    name = f"{user.first_name} {user.last_name}"

    _save(
        {
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "type": "lead",
            "from_id": message.from_id,
            "name": name,
            "service": title,
            "task": task,
            "contact": contact,
        }
    )
    logger.info("Новая заявка от {} по услуге «{}»", message.from_id, title)

    await _notify_admin(
        message,
        "🔔 Новая заявка\n\n"
        f"Услуга: {title}\n"
        f"От: {name} (vk.com/id{message.from_id})\n"
        f"Контакт: {contact}\n\n"
        f"Задача: {task}",
    )
    await message.answer(
        "Спасибо, заявка у меня! Свяжусь с вами в ближайшее время.",
        keyboard=MAIN_MENU,
    )


@labeler.message(payload={"cmd": "review"})
async def review_handler(message: Message) -> None:
    await message.answer(
        "Буду рад обратной связи: напишите, что понравилось или чего не хватает.\n"
        "Чтобы прервать, напишите «отмена»."
    )

    review_message, _ = await wm.wait(labeler.message_view, message, expiration=STEP_TIMEOUT)
    text = (review_message.text or "").strip()
    if _is_cancel(text):
        await message.answer("Хорошо, в другой раз.", keyboard=MAIN_MENU)
        return

    _save(
        {
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "type": "review",
            "from_id": message.from_id,
            "text": text,
        }
    )
    logger.info("Новый отзыв от {}", message.from_id)

    await _notify_admin(message, f"⭐ Отзыв от vk.com/id{message.from_id}:\n\n{text}")
    await message.answer("Спасибо, записал!", keyboard=MAIN_MENU)
