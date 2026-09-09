# 07. Обработка ошибок

Источники: [Обработка ошибок](https://vkbottle.readthedocs.io/ru/latest/tutorial/error-handling/),
[Code-Exception](https://vkbottle.readthedocs.io/ru/latest/low-level/exception_handling/code-exception/),
[Error-Handler](https://vkbottle.readthedocs.io/ru/latest/low-level/exception_handling/error-handler/).

## `VKAPIError`

`VKAPIError` — подтип `CodeException`. Особенность: ошибка идентифицируется в `except`
и без указанного кода (`except VKAPIError`), и при указании кода (`except VKAPIError[code]`).

Два поля:

- `code` — код ошибки, `int`
- `error_msg` — описание ошибки, `str`

```python
from vkbottle import VKAPIError
```

```python
try:
    await api.wall.post()
except VKAPIError as e:
    print("Возникла ошибка", e.code)
```

### Конкретный код: `VKAPIError[code]`

```python
try:
    await api.messages.send(peer_id=1, message="привет!", random_id=0)
except VKAPIError[902] as e:
    print("не могу отправить сообщение из-за настроек приватности")
except VKAPIError as e:
    print("не могу отправить:", e.error_msg)
```

[Список всех ошибок с кодами](https://dev.vk.ru/reference/errors) — в документации ВК.

## Специфичные ошибки

Некоторые ошибки ВК имеют дополнительные поля:

- `CaptchaError`:
  - `captcha_sid` — идентификатор captcha, `str`
  - `captcha_img` — ссылка на изображение, `str`

Обработчик капчи регистрируется прямо на API:

```python
from vkbottle import CaptchaError

bot = ...

async def captcha_handler(e: CaptchaError):
    ...
    return code

bot.api.add_captcha_handler(captcha_handler)
```

## `CodeException` — свои ошибки с кодами

Базовый класс для исключений с кодом — `CodeException`, код указывается
в квадратных скобках (generic-подобный синтаксис).

```python
class MyCodeError(CodeException):
    pass

try:
    raise MyCodeError[1]("Error description")
except MyCodeError[1]:
    print("Error with code 1 appeared")
except MyCodeError[2, 3]:
    print("Error with code 2 or 3 appeared")
except MyCodeError as e:  # Ошибка с любым кодом
    print(f"Error with code {e.code} appeared")
```

## `ErrorHandler`

Четыре метода:

| Метод | Что делает |
| --- | --- |
| `register_error_handler` | декоратор, принимающий типы ошибок и асинхронную функцию-хендлер. Если возникнет одна из указанных ошибок (или её подтипа), исполнится указанный хендлер |
| `register_undefined_error_handler` | декоратор для неизвестных ошибок |
| `handle` | принимает экземпляр ошибки, передаёт в соответствующий хендлер. Если хендлера нет — поднимает ошибку |
| `catch` | декоратор. Ловит ошибки из декорированной функции и передаёт их методу `handle` |

### Отдельный `ErrorHandler`

```python
from vkbottle import ErrorHandler

error_handler = ErrorHandler(redirect_arguments=False, raise_exceptions=False)
# Если redirect_arguments = True, то все аргументы обернутой функции будут поступать и в хендлер исключения
# Если raise_exceptions = True, то все необработанные исключения будут выброшены (игнорируется, если есть обработчик для ненайденных ошибок)

@error_handler.register_error_handler(RuntimeError)
async def exc_handler_runtime(e: RuntimeError):
    print("Oh no runtime error occurred:", e)

@error_handler.register_error_handler(LookupError)
async def exc_handler_lookup(e: LookupError):
    print("Oh no lookup error occurred:", e)
```

Хендлер для ненайденных ошибок:

```python
@error_handler.register_undefined_error_handler
async def exc_handler_undefined(e: Exception):
    print("Oh no unknown error occurred", e)
```

Применение к асинхронной функции:

```python
@error_handler.catch
async def main():
    raise LookupError("I ve lost my keys")
```

```python
import asyncio

asyncio.run(main())
```

Вывод:

```
Oh no lookup error occurred: I've lost my keys
```

### `ErrorHandler` вместе с ботом

У бота уже есть свой хендлер — `bot.error_handler`:

```python
from vkbottle import Bot, VKAPIError

bot = Bot("token")

@bot.error_handler.register_error_handler(RuntimeError)
async def runtime_error_handler(e: RuntimeError):
    print("возникла ошибка runtime", e)

@bot.error_handler.register_error_handler(VKAPIError[902])
async def unable_to_write_handler(e: VKAPIError):
    print("человек не разрешил отправлять сообщения", e)
```

### Один хендлер на несколько типов ошибок

Обратите внимание на распаковку `*VKAPIError[6, 9]`:

```python
from typing import Union
from vkbottle import Bot, VKAPIError

bot = Bot("token")

@bot.error_handler.register_error_handler(TypeError, ValueError)
async def type_or_value_error_handler(e: TypeError | ValueError):
    print("возникла ошибка type или value", e)

@bot.error_handler.register_error_handler(*VKAPIError[6, 9])
async def limit_reached_write_handler(e: VKAPIError):
    print("ой, слишком много запросов", e)
```

Параметр `redirect_arguments: bool` позволяет передавать в хендлер аргументы из
задекорированной через `catch` функции. В связке с ботом это позволяет передать
в хендлер контекстные аргументы из правил и мидлварей.

## Обработка прямо в хендлере

Из официального примера `easy_bot.py` — точечная обработка ошибки 901
(«нельзя отправить сообщение пользователю»):

```python
except VKAPIError[901]:
    logger.error("Can't send message to user with id {}", event.object.user_id)
```

Полезные коды, встречающиеся в документации: `6` и `9` (слишком много запросов),
`901` (нельзя писать пользователю), `902` (запрещено настройками приватности).
