"""Приветствие при вступлении в сообщество и при разрешении сообщений."""

import time

from vkbottle import GroupEventType, GroupTypes, VKAPIError
from vkbottle.modules import logger

from config import WELCOME_MESSAGE, labeler
from keyboards import MAIN_MENU

# group_join и message_allow часто приходят парой, когда человек и подписался,
# и нажал «Начать». Без паузы ушло бы два одинаковых приветствия подряд.
_WELCOME_COOLDOWN_SEC = 30
_last_welcome: dict[int, float] = {}


async def _send_welcome(api, user_id: int, reason: str) -> None:
    now = time.monotonic()
    last = _last_welcome.get(user_id, 0.0)
    if now - last < _WELCOME_COOLDOWN_SEC:
        logger.info("Пропуск повторного приветствия для {} ({})", user_id, reason)
        return

    try:
        users_info = await api.users.get(user_ids=[user_id])
        await api.messages.send(
            peer_id=user_id,
            message=WELCOME_MESSAGE.format(name=users_info[0].first_name),
            keyboard=MAIN_MENU,
            random_id=0,
        )
    except VKAPIError[901]:
        logger.info("Пользователь {} запретил сообщения от сообщества", user_id)
        return

    _last_welcome[user_id] = now
    logger.info("Приветствие отправлено {}, причина: {}", user_id, reason)


@labeler.raw_event(GroupEventType.GROUP_JOIN, dataclass=GroupTypes.GroupJoin)
async def group_join_handler(event: GroupTypes.GroupJoin) -> None:
    user_id = event.object.user_id
    logger.info("Новый участник сообщества: {}", user_id)
    await _send_welcome(event.ctx_api, user_id, "group_join")


@labeler.raw_event(GroupEventType.MESSAGE_ALLOW, dataclass=GroupTypes.MessageAllow)
async def message_allow_handler(event: GroupTypes.MessageAllow) -> None:
    user_id = event.object.user_id
    logger.info("Пользователь {} разрешил сообщения сообщества", user_id)
    await _send_welcome(event.ctx_api, user_id, "message_allow")
