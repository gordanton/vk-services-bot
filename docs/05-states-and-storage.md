# 05. Состояния, Waiter Machine и хранилища

Источники: [State-Dispenser](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/state-dispenser/),
[Waiter Machine](https://vkbottle.readthedocs.io/ru/latest/tools/waiter-machine/),
[Storage](https://vkbottle.readthedocs.io/ru/latest/tools/storage/).

## Когда что использовать

| Инструмент | Для чего |
| --- | --- |
| `StateDispenser` | Ветвистые сценарии: сложное меню, квиз, игра. Состояние живёт долго |
| `WaiterMachine` | Быстрые воронки в рамках одного хендлера, без потери скоупа |
| `CtxStorage` | Просто хранить данные по ключу |

Waiter Machine, в отличие от State Dispenser, **никуда не сериализует состояния**,
поэтому его не следует использовать для сложных стейтов, где важна консистентность
(например транзакции) или которые активны долгое время.

## State Dispenser

Методы:

- `get` — возвращает `StatePeer` (если запись на запрошенный `peer_id` существует) или
  `None`. На вход получает `peer_id`.
- `set` — делает запись. На вход получает `peer_id` и `state`.
- `delete` — удаляет запись. На вход получает `peer_id`.

Получить стейт можно из объекта любого ивента: `event.state_peer.state`.
Ловить пользователей со стейтами в хендлерах можно через `StateRule`
(шорткат `state=`).

```python
from vkbottle import BaseStateGroup
from vkbottle.bot import Message, Bot

bot = Bot("t")

class SuperStates(BaseStateGroup):
    AWKWARD_STATE = "awkward"
    CONFIDENT_STATE = "confident"
    TERRIFYING_STATE = "terrifying"

@bot.on.message(state=SuperStates.AWKWARD_STATE)  # StateRule(SuperStates.AWKWARD_STATE)
async def awkward_handler(message: Message):
    await message.answer("oi awkward")

@bot.on.message(lev="/die")
async def die_handler(message: Message):
    await bot.state_dispenser.set(message.peer_id, SuperStates.AWKWARD_STATE)
    return "ok"

bot.run()
```

### Payload в состоянии

`.set()` может принимать `**payload`, который позже доступен как словарь из
`message.state_peer.payload`:

```python
# ... In handler:
await bot.state_dispenser.set(message.peer_id, SuperStates.TERRIFYING_STATE, something=1)
# ... With state:
print(message.state_peer.payload["something"])  # 1
```

Обратите внимание: в хендлере выше используется `return "ok"` — это работа
return-менеджера, строка отправится как сообщение
(см. [06-middlewares-and-return-managers.md](06-middlewares-and-return-managers.md)).

## Waiter Machine

Создание быстрых воронок без потери скоупа.

```python
from vkbottle.bot import Bot, Message
from vkbottle.tools import WaiterMachine

bot = Bot("...")
wm = WaiterMachine()

@bot.on.message(text="/wm")
async def greeting(message: Message):
    await message.answer("Как тебя зовут?")
    # Следующая строчка остановит выполнение хендлера,
    # и исполнение пойдет дальше только когда будет получено
    # сообщение соответствующее заданным правилам
    # (в данном случае просто от того же пользователя)
    m, _ = await wm.wait(bot.on.message_view, message)
    await message.answer(f"Привет, {m.text.capitalize()}! Будем знакомы.")

bot.run()
```

Из `.wait` возвращается tuple с двумя элементами:

1. Объект события, которое разрешило ожидание (в примере выше — `Message`).
2. Контекст, который был сформирован в ходе обработки события.

Поэтому его можно сразу раскрыть в две переменные.

### Правила и поведение по умолчанию

В `.wait` можно передать правила и `default_behaviour` как именованный аргумент:

```python
await message.answer("Напиши мне твой номер телефона")
m, ctx = await wm.wait(bot.on.message_view, message, RegexRule(PHONE_NUMBER_REGEX), default_behaviour="Неверный формат, напиши еще раз в правильном формате")
```

`default_behaviour` может принимать `Callable`, куда придёт событие, либо любой другой
объект, который будет передан в return-менеджер, привязанный к активному view.
В примере выше это строка, которая будет отправлена как сообщение.

`expiration` принимает `timedelta` или `int` (в секундах), чтобы ограничить время
ожидания. Если ивент придёт позже, чем `start_ts + expiration`, будет вызван `drop`
и ивент обработается в обычном view.

Метод `.drop` используется, чтобы сбросить ожидание ивента по идентификатору.

## Хранилища

Хранилища нужны, чтобы хранить информацию в формате `ключ: значение`.
Все хранилища имеют методы:

- `get(key)`
- `set(key, value)`
- `delete(key)`
- `contains(key)`

### CtxStorage

Контекстное хранилище удобно тем, что его можно открыть и изменить из любого места
в коде, и оно доступно из коробки.

### Своё хранилище

Если нужно хранилище, например, на основе Rabbit MQ:

1. Наследуйтесь от `ABCStorage`.
2. Имплементируйте методы `get`, `set`, `delete` и `contains` с подключением к Rabbit MQ.
