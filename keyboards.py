"""Клавиатуры бота.

Обычная клавиатура (inline=False) вмещает до 40 кнопок в 10 рядах по 5 и
остаётся под полем ввода, поэтому главное меню собираем именно на ней.
Inline-клавиатура ограничена 10 кнопками в 6 рядах и уезжает в историю
переписки — её используем только на экранах услуг.
"""

from vkbottle import Keyboard, KeyboardButtonColor, Text

from services import SERVICES


def _build_main_menu() -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    for service in SERVICES:
        keyboard.add(Text(service.button, {"cmd": "service", "sid": service.id}))
        keyboard.row()
    keyboard.add(
        Text("✉️ Оставить заявку", {"cmd": "lead", "sid": ""}),
        color=KeyboardButtonColor.POSITIVE,
    )
    keyboard.row()
    keyboard.add(Text("⭐ Отзыв или идея", {"cmd": "review"}))
    keyboard.add(Text("👤 Обо мне", {"cmd": "about"}))
    return keyboard.get_json()


# Клавиатура статична, поэтому json собираем один раз при импорте,
# а не на каждое сообщение.
MAIN_MENU = _build_main_menu()


def service_menu(service_id: str) -> str:
    return (
        Keyboard(inline=True)
        .add(
            Text("✉️ Оставить заявку", {"cmd": "lead", "sid": service_id}),
            color=KeyboardButtonColor.POSITIVE,
        )
        .row()
        .add(Text("⬅️ В меню", {"cmd": "menu"}))
    ).get_json()
