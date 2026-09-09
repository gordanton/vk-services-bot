# 06. Мидлвари и return-менеджеры

Источники: [Мидлвари и return менеджеры](https://vkbottle.readthedocs.io/ru/latest/tutorial/middlewares-return-managers/),
[Middleware](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/middleware/),
[Return-Manager](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/return-manager/).

## Мидлвари

Мидлвари — внешние слои, покрывающие обработку хендлеров. У них два состояния:

- `pre` — то, что происходит **до** начала поиска хендлера (когда только нашёлся
  нужный `view`);
- `post` — то, что происходит **после** обработки хендлера, когда известно всё
  о прошедшей обработке: какие хендлеры сработали и что они вернули.

Абстрактный класс — `BaseMiddleware`. Тип ивента указывается в дженерике:

```python
from vkbottle import BaseMiddleware
from vkbottle.bot import Message

class MyMiddleware(BaseMiddleware[Message]):
    ...
```

Для `message_view` это `Message`, а для `raw_event_view` — словарь.

Мидлвари всегда распаковываются из labeler. Конструктор принимает ивент в качестве
аргумента. Методы `pre`/`post` не принимают аргументов и должны возвращать `None`.

Доступные атрибуты:

| Атрибут | Что содержит |
| --- | --- |
| `event` | сам ивент (тип задаётся дженериком) |
| `view: ABCView` | view, с которым был обработан ивент |
| `handle_responses: list` | всё, что вернули хендлеры, по порядку исполнения |
| `handlers: list[ABCHandler]` | все хендлеры, что были исполнены |

Управление обработкой:

- `self.stop(ошибка)` — исполнение view срочно останавливается;
- `self.send({ключ: значение})` — в контекст добавляются аргументы
  (ключ — имя аргумента, попадающего в хендлер).

### `pre`: отсеять сообщения от ботов

```python
from vkbottle.bot import Message
from vkbottle import BaseMiddleware, MiddlewareResponse

class NoBotMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        if self.event.from_id < 0:
            self.stop("from_id меньше 0")
```

### `post`: логи и статистика

`post` уже никак не может повлиять на обработку ивента.

```python
from vkbottle.bot import Message
from vkbottle import BaseMiddleware

class LogMiddleware(BaseMiddleware[Message]):
    async def post(self):
        if not self.handlers:
            return
        print(f"{len(self.handlers)} хендлеров сработало на сообщение. "
              f"Они вернули {self.handle_responses}, "
              f"все они принадлежали к view {self.view}")
```

`pre` и `post` можно использовать одновременно в одном мидлваре.

### Регистрация

Нужно определиться с view, к которому принадлежит мидлварь. Для сообщений это
`MessageView`, в лейблере он лежит по адресу `.message_view`. У каждого view есть
метод `register_middleware`:

```python
bot.labeler.message_view.register_middleware(NoBotMiddleware)
bot.labeler.message_view.register_middleware(LogMiddleware)
```

`register_middleware` можно использовать и как декоратор.
Метод добавляет мидлварь в `view.middlewares`.

## Return-менеджеры

Возвращая значение из хендлера, вы запускаете хендлер return-менеджера, который
выполнит какое-то действие. Для `MessageView` менеджер предустановлен:

| Тип значения | Что произойдёт |
| --- | --- |
| `str` | строка отправится как сообщение |
| `tuple` или `list` | все элементы будут конвертированы в строки и отправлены как сообщения |
| `dict` | словарь распакуется как непозиционные аргументы для метода `message.answer` |

Реализация из документации:

```python
from vkbottle import BaseReturnManager
from vkbottle.bot import Message
from typing import Union

class BotMessageReturnHandler(BaseReturnManager):
    @BaseReturnManager.instance_of(str)
    async def str_handler(self, value: str, message: Message, _: dict[str, Any]):
        await message.answer(value)

    @BaseReturnManager.instance_of((tuple, list))
    async def iter_handler(self, value: tuple | list, message: Message, _: dict[str, Any]):
        [await message.answer(str(e)) for e in value]

    @BaseReturnManager.instance_of(dict)
    async def dict_handler(self, value: dict, message: Message, _: dict[str, Any]):
        await message.answer(**value)
```

Аргументы хендлера return-менеджера: первым приходит само значение, полученное из
хендлера, вторым — объект ивента, третьим — данные из рулзов и мидлварей.
Хендлеры оборачиваются в декоратор `instance_of`, который принимает тип или кортеж
типов.

Для каждого view можно установить свой `handler_return_manager`.
