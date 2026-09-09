# 02. LongPoll API (Polling)

Главный файл для нашего проекта.

Источники: [Polling](https://vkbottle.readthedocs.io/ru/latest/low-level/polling/),
[Bot](https://vkbottle.readthedocs.io/ru/latest/high-level/bot/),
[Handler](https://vkbottle.readthedocs.io/ru/latest/high-level/handling/handler/),
[MessageEvent](https://vkbottle.readthedocs.io/ru/latest/tools/message-event/),
исходники тега `v4.11.0` (`vkbottle/polling/bot_polling.py`, `vkbottle/framework/base.py`)
и официальный пример `examples/high-level/easy_bot.py`.

## Как это устроено

Библиотека использует `Polling`и чтобы реализовывать longpoll. Для ботов и юзеров
создан соответствующий поллинг (так как они разные): `BotPolling` и `UserPolling`.
Свой поллинг можно написать, унаследовав абстрактный `ABCPolling`.

Готовый инстанс доступен как `bot.polling`.

## Методы поллинга

| Метод | Что делает |
| --- | --- |
| `get_server` | Получает сервер для поллинга и возвращает его |
| `get_event` | Получает сервер из `get_server` в параметр и делает долгий POST реквест |
| `listen` | Асинхронный итератор (будет использован с `async with`). Генерирует приходящие ивенты |
| `construct` | Принимает API, нужно чтобы конструировать поллинг с обновлённым API при каждом вызове. Возвращает собственный инстанс, может быть использован в билдер-интерфейсе |

## Параметры `BotPolling` / `UserPolling`

Из документации:

- **api** — если не указано будет получено в `listen`
- **group_id** / **user_id** — если не указано будет получено в `listen`
- **wait** — лимит секунд, после которого вк принудительно возвращает ответ на долгий
  реквест (даже если нет обновлений)
- **rps_delay** — если не указано, задержка равна 0

Фактическая сигнатура `BotPolling` в 4.11.0 (`vkbottle/polling/bot_polling.py`) содержит
ещё два параметра и конкретные значения по умолчанию:

| Параметр | По умолчанию | Примечание |
| --- | --- | --- |
| `api` | `None` | берётся из бота |
| `group_id` | `None` | резолвится через `groups.getById` |
| `wait` | `25`, но не больше `90` | в коде: `min(wait or 25, 90)` |
| `rps_delay` | `0` | |
| `skip_old_events` | `True` | пропускать события, накопившиеся до старта |
| `error_handler` | новый `ErrorHandler()` | |

### `skip_old_events` и восстановление `ts`

При `skip_old_events=False` поллинг сохраняет и восстанавливает `ts` между запусками,
чтобы не терять события, пришедшие пока бот был offline. Состояние лежит в файле
`.vkbottle/bot-polling/{group_id}.json` относительно текущей рабочей директории
(методы `restore_server_ts` / `save_server_ts`).

Если такое поведение нам нужно — не забыть добавить `.vkbottle/` в `.gitignore`.

### Как резолвится `group_id`

`get_server` при отсутствии `group_id` вызывает `groups.getById`, и если групп в ответе
нет, поднимает ошибку с текстом:

> Unable to get group id for bot polling. Perhaps you are using a user access token?

То есть эта ошибка означает, что в бота передан пользовательский токен вместо токена
сообщества.

### Как формируется долгий запрос

`get_event` делает POST на `server["server"]` с параметрами
`act=a_check`, `key`, `ts`, `wait`, `rps_delay` и таймаутом `wait + 10` секунд.

## Запуск

```python
bot.run()
```

- `bot.run_polling()` — асинхронный запуск longpoll (вызывать из уже работающего
  event loop через `await`).
- `bot.run()` — синхронный запуск. Добавляет `run_polling` в таски `bot.loop_wrapper`
  и вызывает `bot.loop_wrapper.run()`.

> На сайте документации в примерах ещё встречается `bot.run_forever()` — в 4.11.0 это
> устаревший псевдоним с `FutureWarning`. Пишем `bot.run()`.

`run_polling` принимает необязательный аргумент `custom_polling`, если нужно
подменить поллинг на свой.

### Важно: события обрабатываются конкурентно

`run_polling` в 4.11.0 для каждого обновления из пачки создаёт отдельную
`asyncio.Task`, поэтому хендлеры разных событий выполняются параллельно и медленный
хендлер не блокирует остальные. Но именно поэтому **нельзя** использовать
блокирующий код внутри хендлеров (см. [10-pitfalls.md](10-pitfalls.md)).

## Настройка сообщества (обязательно)

Если бот не реагирует:

1. В настройках сообщества включён сам Long Poll.
2. Проставлены галочки на нужные типы событий (для сообщений — «Входящие сообщения»).
3. Версия API — стабильная `5.131`. При работе с версией выше у ключа должен быть
   доступ к управлению сообществом.

## Обработка сырых событий: `raw_event`

Встроенные правила работают только с объектами `Message` и `MessageEvent` из
`vkbottle.bot`. Для остальных событий LongPoll используется `@bot.on.raw_event`,
где указывается тип события из `GroupEventType` и dataclass для парсинга.

Из официального примера `easy_bot.py`:

```python
from vkbottle import GroupEventType, GroupTypes, VKAPIError
from vkbottle.modules import logger

@bot.on.raw_event(GroupEventType.GROUP_JOIN, dataclass=GroupTypes.GroupJoin)
async def group_join_handler(event: GroupTypes.GroupJoin):
    try:
        await bot.api.messages.send(
            peer_id=event.object.user_id,
            message="Спасибо за подписку!",
            random_id=0,
        )
    except VKAPIError[901]:
        logger.error("Can't send message to user with id {}", event.object.user_id)
```

Комментарии из того же примера, важные для нас:

> You can use `raw_event` to handle any event type, the advantage is free dataclass,
> for example it can be dict if you have some problems with module types quality.

> Basic API call, please notice that `bot.api` is not accessible in case multibot is
> used, API can be accessed from `event.ctx_api`.

Ещё один пример оттуда — реакции на сообщения:

```python
from vkbottle_types.objects import MessagesForward

@bot.on.raw_event(GroupEventType.MESSAGE_REACTION_EVENT, dataclass=GroupTypes.MessageReactionEvent)
async def reaction_handler(event: GroupTypes.MessageReactionEvent):
    await bot.api.messages.send(
        peer_id=event.object.peer_id,
        message=f"Вы {'поставили' if event.object.reaction_id else 'убрали'} реакцию на это сообщение!",
        forward=MessagesForward(
            conversation_message_ids=[event.object.cmid],
            peer_id=event.object.peer_id,
            is_reply=True,
        ).to_raw(),
        random_id=0,
    )
```

### Callback-кнопки через `raw_event`

Для события `MESSAGE_EVENT` есть удобный dataclass `MessageEvent` из `vkbottle.bot`:

```python
from vkbottle import GroupEventType
from vkbottle.bot import MessageEvent

@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def handle_message_event(event: MessageEvent):
    await event.show_snackbar("Сейчас я исчезну")
```

Подробнее — [04-keyboards-and-attachments.md](04-keyboards-and-attachments.md).

## Свой поллинг

Кастомный поллинг должен унаследовать `ABCPolling` и имплементировать методы
`get_server`, `get_event`, `listen`, `construct`.

## Несколько LongPoll сразу (мультибот)

Мультибот запускает несколько лонгполов на переданных вами API и обрабатывает
получаемые ивенты со всех лонгполов с помощью одного основного бота.

```python
run_multibot(bot, apis, polling_type=BotPolling)
```

`run_multibot` импортируется из `vkbottle.bot`, добавляет `run_polling` в таски и
запускает event loop. Основному боту передавать токен для создания API не нужно.
`apis` — любой итерируемый объект, `polling_type` меняется, если поллинг кастомный.

Внутри хендлеров при мультиботе `bot.api` недоступен — используйте `event.ctx_api`
или `message.ctx_api`.

## LongPoll и Callback API одновременно (dual mode)

Long Poll и Callback API могут работать одновременно: запустите Long Poll через
`bot.run()` (или `await bot.run_polling()`), а события HTTP-сервера, как обычно,
передавайте в `await bot.process_event(event)`. Чтобы обработать одно событие только
один раз, создайте бота с `dual_mode=True`:

```python
bot = Bot(token=TOKEN, callback=callback, dual_mode=True)
```

В этом режиме бот атомарно запоминает событие в локальном TTL-кэше до его передачи
в роутер. По умолчанию запись хранится 300 секунд, а кэш содержит до 10 000 ключей;
параметры можно изменить через `event_deduplication_ttl` и
`event_deduplication_cache_size`. Кэш хранится в памяти процесса, поэтому для
нескольких процессов нужен общий внешний механизм дедупликации.
