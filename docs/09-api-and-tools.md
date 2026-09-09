# 09. API, форматирование, HTTP-клиент, Callback API, логирование

Источники: [API](https://vkbottle.readthedocs.io/ru/latest/low-level/api/),
[FAQ](https://vkbottle.readthedocs.io/ru/latest/tutorial/faq/),
[Formatting](https://vkbottle.readthedocs.io/ru/latest/tools/formatting/),
[HTTP-Client](https://vkbottle.readthedocs.io/ru/latest/low-level/http-client/),
[Callback API (туториал)](https://vkbottle.readthedocs.io/ru/latest/tutorial/callback-bot/),
[Callback API](https://vkbottle.readthedocs.io/ru/latest/low-level/callback/),
[Dependencies customisation](https://vkbottle.readthedocs.io/ru/latest/modules/),
[User](https://vkbottle.readthedocs.io/ru/latest/high-level/user/).

## Какие методы доступны

Всё, что есть в официальной документации ВК. Синтаксис методов, параметры и ошибки
аналогичны, только методы пишутся в `snake_case`, а не `camelCase`:

```python
from vkbottle.api import API

api = API("token")

# https://api.vk.ru/method/account.ban
await api.account.ban(owner_id=1)

# https://api.vk.ru/method/account.getBanned
await api.account.get_banned(offset=0, count=1)
```

Все официальные методы, ответы и ошибки типизированы — используйте IDE с подсказками
и тайпхинты.

## Три способа добраться до API

- `bot.api` — у бота API уже инициализирован, дополнительно создавать не нужно;
- `message.ctx_api` — из объекта сообщения;
- `event.ctx_api` — из сырого события (обязательно при мультиботе).

```python
from vkbottle.bot import Bot, Message

bot = Bot(token="token")
admin_ids = [1, 100]

@bot.on.message(text="админы")
async def who_admins(message: Message):
    admins = [f"{adm.first_name} {adm.last_name}" for adm in (await message.ctx_api.users.get(admin_ids))]
    print((await message.ctx_api.request("users.get", {"user_ids": admin_ids})))
    await message.answer(f"Администраторы этого бота: {' '.join(admins)}")

bot.run()
```

## Метод, которого нет во фреймворке

Используйте `API.request`, `Bot.api.request` или `Message.ctx_api.request`.
Они возвращают **словарь с json-ответом, а не типизированный объект.**

```python
import asyncio
from vkbottle.api import API

api = API("token")

async def main():
    await api.request("users.get", {})  # Single request

    # Multiple request for one session
    async for response in api.request_many(
        [api.APIRequest("users.get", {}), api.APIRequest("groups.get", {})]
    ):
        print(response)

asyncio.run(main())
```

То же через бота:

```python
import asyncio
from vkbottle.bot import Bot

bot = Bot("token")

async def main():
    print(await bot.api.request("users.get", {}))  # Single request

    # Multiple request for one session
    async for response in bot.api.request_many(
        [bot.api.APIRequest("users.get", {}), bot.api.APIRequest("groups.get", {})]
    ):
        print(response)

asyncio.run(main())
```

## Форматированный текст

`Formatter` наследует `str` и имеет два перегруженных метода: `format` и `format_map`.

```python
from vkbottle.tools.formatting import Formatter
```

Доступные типы форматирования: `bold` (полужирный), `italic` (курсив), `url` (ссылка),
`underline` (подчёркнутый). Для каждого типа реализована одноимённая функция,
импортируемая из `vkbottle.tools.formatting`.

```python
Formatter("Hi, {}.").format("Alex")  # Hi, Alex.
Formatter("Hi, {name}.").format(name="Maria")  # Hi, Maria.
```

Специальные идентификаторы — `bold`, `italic`, `underline`:

```python
Formatter("{:bold}, nice formatting!").format("Wow")  # Wow, nice formatting!
Formatter("{framework:italic} has been around for over 5 years!").format(framework="vkbottle")  # vkbottle has been around for over 5 years!
```

Объединение форматов через `+`:

```python
Formatter("Very cool {:bold+italic} ^_^").format("bold-italic message")  # Very cool bold-italic message ^_^
```

`format_map` принимает один аргумент типа `Mapping`:

```python
Formatter("My bestie is {bestie:underline}").format_map({"bestie": "telegrinder")  # My bestie is telegrinder
```

> ⚠️ В документации в этой строке опечатка — не хватает закрывающей `}` у словаря.
> Правильно: `.format_map({"bestie": "telegrinder"})`.

Свойства `Formatter` для получения json: `format_data` (словарь
`{"version": ..., "items": [...]}`) и `raw_format_data` (сырой объект `format_data`).
`format_data` нужен для методов, работающих с форматированным текстом, например
`messages.send`.

Класс `Format` представляет тип форматирования и поддерживает `+=`, конкатенацию строк
и самих типов-форматов:

```python
from vkbottle.tools.formatting import Format
```

```python
bold("Hello, ") + italic("World!")  # Hello, World! ('Hello, ' is bold, 'World!' is italic)
"Hello, " + italic("World!")  # Hello, World! ('World!' is italic)
bold("Hello") + ", " + italic("World!")  # Hello, World! ('Hello' is bold, 'World!' is italic)
bold("vkbottle documentation:") + " " + url(italic("click me"), href="vkbottle.readthedocs.io/ru/latest")  # vkbottle documentation: click me ('click me' has an url)
```

Методы `Format`: `as_data` и `as_raw_data`.

Отправка:

```python
await message.answer(Formatter("Hello, {:bold}!").format("World"))
await message.answer(underline(bold("Hello") + ", " + italic("World!")))
```

В официальном примере `easy_bot.py` (там `Formatter` импортируется просто из `vkbottle`):

```python
@bot.on.message(text="привет мир")
async def hello_handler(message: Message):
    await message.answer(Formatter("Привет, {:bold+italic}!").format("Мир"))
```

## HTTP-клиент

По умолчанию библиотека использует `SingleAiohttpClient` — он всегда использует одну
и ту же сессию.

Методы:

| Метод | Возвращает |
| --- | --- |
| `request_raw` | объект `aiohttp.ClientResponse` |
| `request_text` | строку (поле `text`) |
| `request_json` | словарь, десериализованный из json |
| `request_content` | байты (используется для скачивания медиа в аплоадерах) |

Параметры: `url`, `method` (HTTP-метод, например `get`), `data`, `**kwargs`
(передаются как параметры запроса).

При инициализации `AiohttpClient` можно указать: `session`, `json_processing_module`,
`optimize` (при `True` в конструктор сессии уйдут `raise_for_status=True` и
`skip_auto_headers={"User-Agent"}`), `**session_params` (например `headers`, `cookies`).

```python
from vkbottle.http import AiohttpClient

# ...
http_client = AiohttpClient()
await http_client.request_text("https://google.com")
```

`request_json` десериализует json одной из доступных библиотек, выбираемых через
`choicelib` в порядке слева направо: `json`, `ujson`, `hyperjson`, `orjson`.

Кастомный клиент должен унаследовать `ABCHTTPClient`.

## Callback API

> Обязательно к прочтению: у вас должен иметься собственный сервер с доменным именем.
> DDNS работать не будет. Также подразумевается наличие опыта в настройке веб-серверов.

Для нашего проекта на LongPoll это не нужно, но пусть будет для полноты.

1. Инициализировать параметры:

```python
import os

TOKEN = os.getenv("VK_TOKEN")  # ключ сообщества
url = os.getenv("VK_URL")  # url = "http://example.com/whateveryouwnant"
title = os.getenv("VK_TITLE")  # title = "server"
secret_key = os.getenv("VK_SECRET_KEY")  # опционально
```

2. Импортировать `BotCallback` и указать параметры:

```python
from vkbottle.callback import BotCallback

callback = BotCallback(
    url = url,
    title = title
)
```

3. Инициализировать бота:

```python
from vkbottle import Bot

bot = Bot(token=TOKEN, callback=callback)
```

4. Настроить любой сервер (`aiohttp`, `flask`, `fastapi`) и обрабатывать события:

```python
# event - событие, полученное от vk
await bot.process_event(event)
```

> После подключения бот будет обрабатывать входящие сообщения, для получения остальных
> событий необходимо включить их в настройках группы.

Параметры `BotCallback`: `url` (сервер, на который будут отправляться события),
`title` (короткое имя сервера в настройках сообщества), `secret_key` (секретный ключ
для проверки источника; по умолчанию генерируется произвольная строка), `api`,
`group_id`.

Методы работы с Callback API: `add_callback_server`, `delete_callback_server`,
`edit_callback_server`, `get_callback_confirmation_code`, `get_callback_servers`,
`get_callback_settings`, `set_callback_settings`, `construct`.

Одновременная работа с LongPoll — см. раздел про dual mode в
[02-longpoll.md](02-longpoll.md).

## Логирование и зависимости

VKBottle автоматически выбирает лучшую альтернативу для стандартных библиотек.
Эти библиотеки не указаны в зависимостях, поэтому устанавливать их нужно самим.

- **JSON**, в порядке убывания приоритета: `orjson`, `hyperjson`, `ujson`, `json`
- **Logging**, в порядке убывания: `loguru`, `logging`

> Настоятельно рекомендуется использовать `loguru` вместо `logging`. Возможно, он
> станет обязательной зависимостью в будущих релизах.

По умолчанию уровень логирования выставлен на `DEBUG`. Изменить его можно так.

Через `logging`:

```python
import logging
logging.getLogger("vkbottle").setLevel(logging.INFO)
```

Через `loguru` — установить определённый уровень:

```python
import sys
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="INFO")
```

Или установить переменную окружения `LOGURU_LEVEL`.

Отключить логирование полностью:

```python
from loguru import logger
logger.disable("vkbottle")
```

Логгер фреймворка доступен как `from vkbottle.modules import logger` и использует
brace-стиль подстановки:

```python
logger.error("Can't send message to user with id {}", event.object.user_id)
```

## Токены

- **Токен пользователя:** самый простой способ — воспользоваться сервисом
  [vkhost.github.io](https://vkhost.github.io).
- **Токен бота (сообщества):** у токена сообщества доступны не все методы,
  в отличие от токена пользователя — учитывайте это.

## Про `User` (юзербот)

`User` реализован «буквально для галочки». Его использование запрещено сразу
несколькими правилами ВКонтакте (п. **6.3.9** и **6.7**), и авторы фреймворка
не несут ответственности за аккаунты и не обязуются помогать с проблемами.

Импортировать составляющие можно из `vkbottle.user`: `User`, `Blueprint`,
`UserLabeler`, `Message`, `run_multibot`, `views`. Всё остальное идентично обычным
ботам. Причина ограничений — большая разница между `User Long Poll API` и
`Bot Long Poll API`.

**Для нашего проекта используем только `Bot` с токеном сообщества.**

## Изменения версий, важные для кода

Из раздела «Что нового»:

**4.2**

- Параметры вида `user_id` или `peer_id` удалены из `Message.answer()`.
  `Message.answer()` подразумевает ответ на текущее сообщение; чтобы ответить
  в другой чат, используйте `API.messages.send`.
- Появилась встроенная поддержка Callback API.

**4.3**

- `Message.get_full_message()` — получает полное сообщение из беседы по его
  `conversation_message_id`. Полезно при работе с аттачментами: позволяет получить
  рабочие `access_key` или полное сообщение, если `Message.is_cropped == False`.
  Обновляет текущий объект и возвращает его.
- `Message.get_attachment_strings()` — получить аттачменты в виде строк для отправки.
  Желательно использовать вместе с `Message.get_full_message()`.
- `Message.reply_message` и `Message.fwd_messages` заменяются на новый объект
  `ForeignMessageMin` с такими же шорткатами, как у `Message`.
- Все объекты в `vkbottle-types` теперь неизменяемы, благодаря этому они хешируемы
  и их можно использовать в `set`.
