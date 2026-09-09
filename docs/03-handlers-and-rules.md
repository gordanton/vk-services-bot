# 03. Хендлеры, лейблер и правила

Источники: [Handler](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/handler/),
[Bot-Labeler](https://vkbottle.readthedocs.io/ru/latest/high-level/bot/labeler/),
[Правила (туториал)](https://vkbottle.readthedocs.io/ru/latest/tutorial/rules/),
[Все встроенные правила](https://vkbottle.readthedocs.io/ru/latest/high-level/builtin-rules/),
[Rules](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/rules/),
[View](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/view/),
[Router](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/router/).

## Хендлеры

Хендлеры — конечная точка в обработке событий. Они бывают блокирующими (если нашёлся
подходящий хендлер, другие уже не проверяются и не выполняются) и неблокирующими
(количество выполняемых хендлеров не ограничено). **По умолчанию все хендлеры
являются блокирующими.**

```python
from vkbottle.bot import Bot, Message

bot = Bot("token")

@bot.on.message()
async def any_message(message: Message):
    await message.answer("Привет я бот")

bot.run()
```

Типы хендлеров для сообщений: `message`, `chat_message`, `private_message`
(см. таблицу в [01-quickstart.md](01-quickstart.md)).

### Аргументы из правил распаковываются в хендлер

Если правило вернуло словарь, он будет распакован и передан в качестве аргументов
в хендлер, если тот их принимает:

```python
# Кастомное правило MyRule возвращает словарь `{"some_key": "some_value"}`
@bot.on.message(MyRule())
async def some_key_handler(message: Message, some_key: str):
    await message.answer(f"some_key={some_value}")

@bot.on.message(MyRule())
async def regular_handler(message: Message):
    await message.answer("Этот хендлер не принимает аргумент 'some_key', поэтому он и не был передан")

@bot.on.message(MyRule())
async def kwargs_handler(message: Message, **kwargs: Any):
    await message.answer(f"В хендлере переданы аргументы: {kwargs}")
    # В хендлере переданы аргументы: {"some_key": "some_value"}
```

### Несколько наборов правил на один хендлер

Из официального примера `easy_bot.py`:

> If you need to make handler respond for 2 different rule set you can use double
> decorator like here it is or use filters (`OrRule` here).

```python
@bot.on.message(text=["/съесть <item>", "/съесть"])
@bot.on.message(payload={"cmd": "eat"})
async def eat_handler(message: Message, item: str | None = None):
    if item is None:
        item = random.choice(EATABLE)
    await message.answer(f"Ты съел <<{item}>>!", keyboard=KEYBOARD)
```

## Лейблер

Лейблер — удобная оболочка над роутерами. С помощью лейблера создаются хендлеры.
Может быть использован в качестве портабельного диспатчера.

Имеет метод `load`, который загружает хендлеры и мидлвари в текущий лейблер из
переданного — это основной способ разбить код на части
(см. [08-project-structure.md](08-project-structure.md)).

```python
from vkbottle import Bot
from routes import labelers

bot = Bot("token")

for custom_labeler in labelers:
    bot.labeler.load(custom_labeler)

bot.run()
```

```python
from vkbottle.bot import BotLabeler, Message

bl = BotLabeler()

@bl.message(text=["привет", "хай", "здравствуй"])
async def greeting(message: Message):
    await message.answer("Привет, друг")
```

Полезные атрибуты лейблера, встречающиеся в документации и примерах:

- `labeler.custom_rules` — реестр шорткатов правил;
- `labeler.auto_rules` — правила, накладываемые на все хендлеры сообщений этого лейблера;
- `labeler.raw_event_auto_rules` — то же для сырых событий;
- `labeler.vbml_ignore_case` — игнорировать регистр в текстовых паттернах;
- `labeler.message_view` — `MessageView`, к которому регистрируются мидлвари;
- `labeler.message_view.replace_mention` — нужно выставить в `True`, чтобы работало
  правило `mention`.

## Два способа применять правила

**1. Импортировать класс правила** из `vkbottle.dispatch.rules.base` и инициализировать
прямо в декораторе:

```python
from vkbottle.dispatch.rules.base import CommandRule

@bot.on.message(CommandRule("say", ["!", "/"], 1))
async def say_handler(message: Message, args: tuple[str]):
    await message.answer(f"<<{args[0]}>>")
```

**2. Использовать шорткат** — именованный аргумент декоратора:

```python
@bot.on.message(command=("say", 1))
async def say_handler(message: Message, args: tuple[str]):
    await message.answer(f"<<{args[0]}>>")
```

Некоторые правила принимают итерируемый объект. Например, `CommandRule` принимает
`command` и `args_count`, но при использовании шортката их можно передавать
в кортеже: `@bot.on.message(command=("help", 0))`.

> Все встроенные рулзы работают только с объектами `Message` и `MessageEvent` из
> `vkbottle.bot`. Для обработки сырых евентов нужно писать свою реализацию.

## Шорткаты правил

| Шорткат | Правило |
| --- | --- |
| `from_chat` | `PeerRule` |
| `mention` | `MentionRule` |
| `command` | `CommandRule` |
| `from_user` | `FromUserRule` |
| `peer_ids` | `FromPeerRule` |
| `sticker` | `StickerRule` |
| `attachment` | `AttachmentTypeRule` |
| `levenshtein`, `lev` | `LevenshteinRule` |
| `length` | `MessageLengthRule` |
| `action` | `ChatActionRule` |
| `payload` | `PayloadRule` |
| `payload_contains` | `PayloadContainsRule` |
| `payload_map` | `PayloadMapRule` |
| `func` | `FuncRule` |
| `coroutine`, `coro` | `CoroutineRule` |
| `state` | `StateRule` |
| `state_group` | `StateGroupRule` |
| `regexp`, `regex` | `RegexRule` |
| `macro` | `MacroRule` |
| `text` | `VBMLRule` |
| `fuzzy` | `FuzzyTextRule` |

## Все встроенные правила

### `PeerRule(from_chat: bool = True)`
Ограничение источника сообщения. `PeerRule(from_chat=False)` указывает, что сообщение
должно быть из личного диалога с ботом.

### `MentionRule(mention_only: bool = False)`
Проверка, что бот был упомянут в сообщении. `mention_only` означает, что кроме
упоминания в сообщении быть ничего не должно; иначе упоминание удаляется из сообщения,
чтобы другие правила могли обработать сам текст.

### `CommandRule`
```
CommandRule(
    command_text,
    prefixes,
    args_count = 0,
    sep = " "
)
```
Команда выглядит так:
```
{prefix}{command_text}{sep.join(args)}
```
В `command_text` можно передать несколько вариантов названия команды, в `prefixes` —
несколько возможных префиксов (например `'/'`, `'!'`). В `args_count` передаётся
количество обязательных аргументов с `sep` в качестве разделителя.

### `VBMLRule`
```
VBMLRule(pattern, patcher=None, flags=None)
```
Парсер текстов сообщений на разметке [vbml](https://github.com/tesseradecade/vbml),
сделанной специально для фреймворка — позволяет писать паттерны с валидируемыми
аргументами.

```python
rule = VBMLRule("/cmd <eggs:int>")
rst = await rule.check(Message(text="/cmd 11", ...))
assert rst == {"eggs": 11}
```

Это правило стоит за шорткатом `text`, то есть `text="привет"` — это VBML-паттерн.

### `RegexRule(regexp)`
Проверка текста сообщения на соответствие регулярному выражению.

### `StickerRule(sticker_ids = None)`
Отлов стикеров. Если `sticker_ids = None`, проходит любое сообщение со стикером.

### `FromPeerRule(peer_ids)`
Сообщения, отправленные пользователем/группой с одним из указанных ID.

### `AttachementTypeRule(attachment_types)`
Сообщения с указанным типом вложений (например `photo`).

### `ForwardMessagesRule`
Проверяет, что сообщение содержит в себе вложенные сообщения.

### `ReplyMessageRule(reply_message: bool = True)`
Проверка наличия сообщения-ответа.

### `GeoRule`
Отлов сообщений с геометкой.

### `LevenshteinRule(levenshtein_texts, max_distance: int = 1)`
Fuzzy string matching. `max_distance` — максимальное отклонение от заданного текста.

> **Deprecation:** обсуждается удаление этого правила из новых версий из-за
> неоптимальности. Вместо него рекомендуется `FuzzyTextRule`.

### `FuzzyTextRule(texts, min_ratio: float = 0.7)`
Fuzzy string matching. `min_ratio` — минимальная похожесть сообщения с переданным
текстом (от 0 до 1).

### `MessageLengthRule(min_length: int)`
Ограничение минимальной длины текстового сообщения.

### `ChatActionRule(chat_action_types)`
Отлов событий в беседах (например `chat_invite_user`).

### `PayloadRule(payload)`
Проверяет, что payload сообщения равен одному из данных.

### `PayloadContainsRule(payload_part)`
Проверяет, что payload сообщения содержит данную часть.

### `PayloadMapRule(payload_map)`
Ассоциация нужных значений и типов в payload сообщений. Такой payload:

```python
{"name": "boba", "data": {"action": "do", "number": 12}}
```

выражается таким payload map:

```python
PayloadMapRule({"name": str, "data": {"action": str, "number": int}})
```

Вместо типа данных можно передать валидатор (`ABCValidator`), функцию (она будет
вызвана со значением из полезной нагрузки) или literal-значение:

```python
PayloadMapRule(
    {
        "name": "boba",
        "data": {
            "action": lambda x: x in ("do", "undo"),
            "number": int,
        }
    }
)
```

### `FromUserRule(from_user: bool = True)`
Проверка, что сообщение отправлено пользователем, а не ботом. При `from_user = False`
работает наоборот.

### `FuncRule(func)`
Принимает функцию, вызываемую с единственным аргументом — событием. Функция должна
вернуть `bool` или `dict` с обновлением контекста.

### `CoroutineRule(coro)`
Ответ проверки получается из переданной корутины.

### `StateRule(state)`
Для стейт-машины: проверяет, что источник ивента находится в переданном состоянии.
Если состояние `None`, проверяет, что источник не находится ни в каком состоянии.

### `StateGroupRule(state_group)`
Проверяет, что пользователь находится в нужной коллекции состояний.

## Свои правила

Правило — это класс, соответствующий интерфейсу `ABCRule`, который должен реализовать
лишь один асинхронный метод `check`, принимающий ивент и возвращающий `False`, если
проверка не пройдена, и `True` либо словарь с аргументами, которые будут распакованы
в хендлер как непозиционные аргументы.

```python
from typing import Union
from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule

class MyRule(ABCRule[Message]):
    async def check(self, event: Message) -> bool:
        return len(event.text) < 100
```

Использование первым способом:

```python
@bot.on.message(MyRule())
```

Чтобы правило работало и шорткатом, добавьте параметры через `__init__`:

```python
# Новый вид правила
class MyRule(ABCRule[Message]):
    def __init__(self, lt: int = 100):
        self.lt = lt

    async def check(self, event: Message) -> bool:
        return len(event.text) < self.lt
```

и зарегистрируйте его в лейблер **до объявления хендлеров**:

```python
bot.labeler.custom_rules["my_rule"] = MyRule
```

после чего доступно:

```python
@bot.on.message(my_rule=50)
```

### Правила-врапперы

Правила, которые исполняют код, полученный в параметрах. Из коробки: `func`
(шорткат для `FuncRule`) и `coro`/`coroutine` (шорткат для `CoroutineRule`).
`FuncRule` принимает функцию, которая может быть лямбдой, поэтому правило `MyRule`
выше заменяется одной строкой:

```python
@bot.on.message(func=lambda message: len(message.text) < 100)
```

## View и Router (для общего понимания)

**View** — блокирующие менеджеры хендлеров. Если `process_event` у view вернул `True`,
другие view уже не будут проверяться. Сначала обрабатывается `process_view`, который
должен вернуть boolean; если `True` — поиск view прекращается и вызывается
`handle_event`, отвечающий за подбор хендлера.

У каждого view минимум 4 атрибута: `handlers` (лист из `ABCHandler`), `middlewares`
(сет из классов `BaseMiddleware`), `middleware_instances`, `handler_return_manager`.

**Router** — компонент, который принимает запрос и передаёт его в подходящий view,
а также перехватывает ошибки, возникающие во время выполнения view. Атрибуты:
`views`, `state_dispenser`, `error_handler`. Методы: `route`, `construct`, `add_view`,
`view` (декоратор).

Полный пример написания своего view для события `poll_vote_new` есть на
[странице View](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/view/) —
нам он, скорее всего, не понадобится, так как для нестандартных событий проще
использовать `@bot.on.raw_event` (см. [02-longpoll.md](02-longpoll.md)).
