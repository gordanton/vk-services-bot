# 01. Быстрый старт: API и первый бот

Источники: [Первый бот на vkbottle](https://vkbottle.readthedocs.io/ru/latest/tutorial/first-bot/),
[Bot](https://vkbottle.readthedocs.io/ru/latest/high-level/bot/),
[API](https://vkbottle.readthedocs.io/ru/latest/low-level/api/).

## Установка

```
pip install vkbottle
```

Требуется Python `>=3.10, <4.0`.

## Объект `API`

`API` — готовый инструмент для запросов к API ВКонтакте с полной типизацией
(типы живут в отдельном пакете [@vkbottle/types](https://github.com/vkbottle/types)).

```python
from vkbottle import API
```

Для инициализации нужна строка (токен) либо список строк (токенов) — список
автоматически конвертируется в специальный token-generator.

Все методы вызываются через `await` и записываются в `snake_case`, а не `camelCase`:

```python
from vkbottle import API

# ...
api = API(token="token")
await api.messages.send(peer_id=1, message="Привет Павел Дуров!")
```

Полный пример с запуском асинхронного кода:

```python
import asyncio
from vkbottle import API

async def main():
    api = API("token")
    await api.wall.post(message="#vkbottle прекрасен!")

asyncio.run(main())
```

Параметры запроса передаются обычными именованными аргументами — IDE подскажет их
по типам, поэтому в документацию VK API заглядывать почти не нужно.

## Первый бот

`Bot` — класс **исключительно для групп**. Для юзербота есть отдельный `User`
(см. [09-api-and-tools.md](09-api-and-tools.md), использовать не рекомендуется).

```python
from vkbottle.bot import Bot
```

Обязателен один из аргументов — `token` **или** `api`. Если передать `token`,
будет создан `API` с соответствующим генератором токена; если передать `api` —
использоваться будет он:

```python
# Инициализация токеном
bot = Bot(token="token")
# (или) Инициализация с апи
bot = Bot(api=api)
```

Хендлеры добавляются через лейблер: `bot.labeler` или его псевдоним `bot.on`
(`.on` существует для красоты и совместимости с legacy-стилем vkbottle 2.x).

```python
from vkbottle.bot import Bot, Message

bot = Bot(token="token")

@bot.on.message(text="Привет")
async def hi_handler(message: Message):
    users_info = await bot.api.users.get(message.from_id)
    await message.answer("Привет, {}".format(users_info[0].first_name))

bot.run()
```

Разбор по строкам (из документации):

- `@bot.on.message(text="Привет")` — декоратор: если сообщение отвечает заданным
  правилам, срабатывает хендлер под декоратором.
- `async def hi_handler(message: Message)` — объявление хендлера. Имя функции любое,
  аргумент `message` обязательно вернётся в хендлер и содержит информацию о событии.
- `users_info = await bot.api.users.get(message.from_id)` — запрос к API, получение
  информации о пользователе, написавшем сообщение.
- `await message.answer(...)` — отправка сообщения в чат. `answer` — шорткат для ответа:
  аргументы идентичны методу `messages.send`, но не требуются id чата и `random_id`.
- `bot.run()` — помогает асинхронно запустить бота из синхронной среды. Если среда уже
  асинхронная, используйте `await bot.run_polling()`.

## Три декоратора для сообщений

| Декоратор | Что обрабатывает |
| --- | --- |
| `.message` | сообщения и из бесед, и из личных переписок |
| `.private_message` | только личные переписки |
| `.chat_message` | только беседы |

Ничего необычного они не делают — просто подставляют предустановленное `PeerRule`:
в `message` оно не предустановлено, в `chat_message` — `PeerRule(True)`,
в `private_message` — `PeerRule(False)`.

## Атрибуты бота

| Атрибут | Документация |
| --- | --- |
| `bot.api` | [API](09-api-and-tools.md) |
| `bot.router` | Router |
| `bot.labeler` / `bot.on` | [Labeler](03-handlers-and-rules.md) |
| `bot.polling` | [Polling](02-longpoll.md) |
| `bot.callback` | [Callback](09-api-and-tools.md) |
| `bot.error_handler` | [Error handler](07-error-handling.md) |
| `bot.loop_wrapper` | [Loop Wrapper](08-project-structure.md) |

## Методы запуска

### Long Poll API

- `bot.run_polling()` — асинхронный запуск longpoll.
- `bot.run()` — синхронный запуск longpoll. Добавляет `run_polling` в таски
  `bot.loop_wrapper` и вызывает `bot.loop_wrapper.run()`.

### Callback API

- `bot.setup_webhook()` — устанавливает сервер для `CallbackAPI` в сообщество.
- `bot.process_event(event)` — передаёт полученное событие в роутер для обработки.

## Если бот не отвечает

Проверьте, что в настройках сообщества включён сам Long Poll и поставлены галочки
на нужные события (в примере выше — на новые сообщения). Стабильная версия — `5.131`.
При работе с версией выше у ключа должен быть доступ к управлению сообществом.

Подробнее — [02-longpoll.md](02-longpoll.md).
