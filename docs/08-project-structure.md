# 08. Структура проекта, лейблеры, мультибот, LoopWrapper

Источники: [Разделение кода](https://vkbottle.readthedocs.io/ru/latest/tutorial/code-separation/),
[Bot-Labeler](https://vkbottle.readthedocs.io/ru/latest/high-level/bot/labeler/),
[Bot-Multibot](https://vkbottle.readthedocs.io/ru/latest/high-level/bot/multibot/),
[Bot-Blueprint](https://vkbottle.readthedocs.io/ru/latest/high-level/bot/blueprint/),
[Loop Wrapper](https://vkbottle.readthedocs.io/ru/latest/tools/loop-wrapper/).

## Blueprint устарел

> Блупринты являются устаревшей частью фреймворка и будут удалены в следующих версиях.

Для разделения кода используем лейблеры (ниже).

## Рекомендуемая иерархия файлов

```text
/src/
├── handlers
│   ├── __init__.py
│   ├── admin.py
│   ├── chat.py
│   └── ping.py
├── bot.py
└── config.py
```

Смысл подхода: составляющие фреймворка можно использовать отдельно от `Bot`.
Кроме того, разделение кода позволяет делать локальные изменения в лейблере —
например `auto_rules` устанавливает правила, накладываемые на все хендлеры сообщений
этого лейблера.

> ⚠️ Правила в `auto_rules` распространяются только на хендлеры сообщений. Для сырых
> евентов нужен `raw_event_auto_rules` и кастомные правила, работающие с ними.

## `config.py`

Файл с конфигом, где хранятся все глобальные переменные, используемые в разных частях
проекта:

```python
from vkbottle import API, BuiltinStateDispenser
from vkbottle.bot import BotLabeler


api = API("token")
labeler = BotLabeler()
state_dispenser = BuiltinStateDispenser()
```

В этом примере стейт-диспенсер не используется, но объявлен для наглядности. Если он
нужен — импортируйте из `config.py` и используйте в хендлерах, и не забудьте указать
`state_dispenser` в `Bot` в `bot.py`.

> В нашем проекте вместо строки `"token"` токен читаем из `.env` через `load_dotenv()`.

## `handlers/ping.py` — простейший хендлер на общем лейблере

```python
from config import labeler


@labeler.message(text="ping")
async def ping_handler(message):
    await message.answer("pong")
```

## `handlers/chat.py` — свой лейблер с `auto_rules`

Здесь: правило, следящее чтобы все сообщения шли только из чата, плюс правило,
получающее информацию о чате и возвращающее её для всех хендлеров этого лейблера.

```python
from vkbottle.bot import BotLabeler, Message, rules
from vkbottle_types.objects import MessagesConversation


class ChatInfoRule(rules.ABCRule[Message]):
    async def check(self, message: Message) -> dict[str, Any]:
        chats_info = await message.ctx_api.messages.get_conversations_by_id(message.peer_id)
        return {"chat": chats_info.items[0]}


chat_labeler = BotLabeler()
chat_labeler.vbml_ignore_case = True
chat_labeler.auto_rules = [rules.PeerRule(from_chat=True), ChatInfoRule()]


@chat_labeler.message(command="самобан")
async def kick(message: Message, chat: MessagesConversation):
    await message.ctx_api.messages.remove_chat_user(message.chat_id, message.from_id)
    await message.answer(
        f"Участник самоустранился из {chat.chat_settings.title} по собственному желанию"
    )


@chat_labeler.message(text="где я")
async def where_am_i(message: Message, chat: MessagesConversation):
    await message.answer(f"Вы в <<{chat.chat_settings.title}>>")
```

Обратите внимание: `ChatInfoRule` возвращает словарь `{"chat": ...}`, и ключ `chat`
автоматически приходит в хендлеры как аргумент.

## `handlers/admin.py` — команды только для владельца

```python
from vkbottle.bot import BotLabeler, Message, rules

admin_labeler = BotLabeler()
admin_labeler.auto_rules = [rules.FromPeerRule(1)]  # Допустим, вы являетесь Павлом Дуровым


@admin_labeler.message(command="halt")
async def halt(_):
    exit(0)
```

## `handlers/__init__.py` — сбор лейблеров

```python
from .chat import chat_labeler
from .admin import admin_labeler
from .ping import labeler
# Если использовать глобальный лейблер, то все хендлеры будут зарегистрированы в том же порядке, в котором они были импортированы

__all__ = ("admin_labeler", "chat_labeler", "labeler")
```

## `bot.py` — сборка и запуск

```python
from vkbottle import Bot
from config import api, state_dispenser, labeler
from handlers import chat_labeler, admin_labeler
```

Загрузка хендлеров в глобальный лейблер:

```python
labeler.load(chat_labeler)
labeler.load(admin_labeler)
```

Создание инстанса бота с указанием лейблера и стейт-диспенсера:

```python
bot = Bot(
    api=api,
    labeler=labeler,
    state_dispenser=state_dispenser,
)
```

Запуск:

```python
bot.run()
```

### Альтернатива: список лейблеров в цикле

```python
from vkbottle import Bot
from routes import labelers

bot = Bot("token")

for custom_labeler in labelers:
    bot.labeler.load(custom_labeler)

bot.run()
```

```python
from . import greetings, goodbyes

labelers = [greetings.bl, goodbyes.bl]
```

## Мультибот

Мультибот запускает несколько лонгполов на переданных API и обрабатывает ивенты
со всех лонгполов одним основным ботом. `run_multibot` импортируется из `vkbottle.bot`,
добавляет `run_polling` в таски и запускает event loop.

```python
run_multibot(bot, apis, polling_type=BotPolling)
```

- основному боту передавать токен для создания API не нужно;
- `apis` — любой итерируемый объект (можно сделать свой генератор);
- `polling_type` меняется, если поллинг кастомизирован.

При мультиботе `bot.api` в хендлерах недоступен — используйте `event.ctx_api`
или `message.ctx_api`.

## LoopWrapper

`LoopWrapper` нужен, чтобы контролировать event loop для работы с asyncio и хранить
основные таски, `startup` и `shutdown`, которые будут исполнены только при запуске
event loop.

> Если вы используете `LoopWrapper` вместе с `Bot`, учтите, что `Bot` уже имеет свой
> `LoopWrapper`, доступный по пути `bot.loop_wrapper` и запускающийся при вызове
> `bot.run()`.

### Таски

```python
from vkbottle import LoopWrapper

async def my_task():
    ...

lw = LoopWrapper()
lw.add_task(my_task())
lw.run()
```

### `on_startup` и `on_shutdown`

Корутины `on_startup` запустятся перед запуском event loop, `on_shutdown` — при
остановке. В экземпляре это списки с корутинами:

```python
from vkbottle import LoopWrapper

async def startup_task():
    print("This is startup")

async def shutdown_task():
    print("This is shutdown")

lw = LoopWrapper()
lw.on_startup.append(startup_task())
lw.on_shutdown.append(shutdown_task())
lw.run()
```

### `interval` — повторяющиеся задачи

Пригодится для рассылок и периодических проверок:

```python
from vkbottle import LoopWrapper

lw = LoopWrapper()

@lw.interval(seconds=10)
async def repeated_task():
    print("I'll print this every 10 seconds!")

lw.run()
```

### `timer` — отложенная задача

```python
from vkbottle import LoopWrapper

lw = LoopWrapper()

@lw.timer(seconds=10)
async def delayed_task():
    print("I'll print this after 10 seconds!")

lw.run()
```
