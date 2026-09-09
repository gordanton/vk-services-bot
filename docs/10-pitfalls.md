# 10. Подводные камни

Источник: [FAQ](https://vkbottle.readthedocs.io/ru/latest/tutorial/faq/) и разделы
документации, отмеченные предупреждениями.

## Асинхронность

`await` пишется **только внутри `async` функций** и больше нигде.

Плохо:

```python
# bad
async def foo() -> str:
    return "foo"

def main():
    print(await foo())  # SyntaxError: 'await' outside async function

main()
```

```python
# bad
async def main():
    print("main")

await main()  # SyntaxError: 'await' outside function
```

Хорошо:

```python
# good
import asyncio

async def foo() -> str:
    return "foo"

async def main():
    print(await foo())

asyncio.run(main())
```

Не забывайте `await` перед вызовом async-функции, иначе она не запустится:

```python
import asyncio

async def get_banana() -> str:
    return "banana"

async def main():
    print(get_banana())
    # <coroutine object get_banana at 0x0000024BABF48C40>
    print(await get_banana())
    # banana

asyncio.run(main())
```

## Блокировки — главная причина «зависшего» бота

В асинхронном программировании блокирующие функции — это все функции без `await`,
работающие на принципе IO. Если заблокируете выполнение надолго, бот зависнет,
потому что не остановил функцию в нужный момент, чтобы выполнять другие сопрограммы.

### `time.sleep` → `asyncio.sleep`

```python
# bad
time.sleep(10)
```

```python
# good
await asyncio.sleep(10)
```

### `requests` → `aiohttp` / встроенный клиент

Распространённая проблема — модуль `requests`, `urllib3` и производные
API-обёртки (`vk_api` и т.п.). Они хороши для неасинхронного кода, но запрос может
идти долго, и бот из-за этого зависнет.

```python
# bad
async def send_httpbin_get() -> dict[str, Any]:
    r = requests.get('http://httpbin.org/get')
    if r.status_code == 200:
        js = r.model_dump_json()
        return js
```

```python
# good, recommended
# see https://vkbottle.rtfd.io/ru/latest/low-level/http-client/
from vkbottle.http import AiohttpClient

async def send_httpbin_get() -> dict[str, Any]:
    http_client = AiohttpClient()
    return await http_client.request_json('http://httpbin.org/get')
```

```python
# good
import aiohttp

async def send_httpbin_get() -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get('http://httpbin.org/get') as r:
            if r.status == 200:
                js = await r.json()
                return js
```

`aiohttp` идёт зависимостью в vkbottle.

## `pydantic.error_wrappers.ValidationError`

Объекты фреймворка типизированы и генерируются на основе официальной VK-API схемы.
ВК обновляет её без предупреждений, из-за чего могут произойти поломки с валидацией.

Если ошибка произошла, попробуйте обновить типы:

```
pip install git+https://github.com/vkbottle/types -U
```

Если не помогло — issue в репозиторий `vkbottle` (не `types`) или в чат ВК/Телеграм.

## Чек-лист «бот не отвечает»

1. В настройках сообщества включён Long Poll и проставлены галочки на нужные события.
2. Версия API — `5.131`. Для версий выше у ключа нужен доступ к управлению сообществом.
3. Используется токен **сообщества**, а не пользователя. Иначе поллинг падает с
   `Unable to get group id for bot polling. Perhaps you are using a user access token?`
4. Хендлеры зарегистрированы **до** запуска, а кастомные правила добавлены в
   `labeler.custom_rules` до объявления хендлеров.
5. Помните, что хендлеры по умолчанию блокирующие: если раньше в цепочке сработал
   более общий хендлер (например `@bot.on.message()` без правил), до нужного дело
   не дойдёт. Порядок регистрации имеет значение.
6. Для правила `mention` нужно выставить `bot.labeler.message_view.replace_mention = True`.

## Мелкие расхождения в самой документации

Замечены при сверке сайта, исходных `.md` версии 4.11.0 и кода — чтобы не спотыкаться:

| Где | Что |
| --- | --- |
| Примеры на сайте | `bot.run_forever()` — устарело, пишем `bot.run()` |
| Пример аплоадера | аргумент хендлера `message`, а внутри `m.peer_id` |
| Пример `format_map` | не хватает закрывающей `}` у словаря |
| Имя класса правила | в списке правил — `AttachementTypeRule` (так в коде), в списке шорткатов — `AttachmentTypeRule`; шорткат называется `attachment` |
| Туториал по шаблонам | `template_gen` импортируется из `vkbottle.tools`, в разделе Tools — из `vkbottle` |
| Примеры с `users.get` | В документации `await bot.api.users.get(message.from_id)`, но в `vkbottle-types` 5.199.x первый параметр метода — `fields`, а не id. Нужно `users.get(user_ids=[message.from_id])`, иначе id уйдёт в `fields` |

## Что почитать по asyncio

В документации прямо сказано: в Python написание async-кода требует такого же
освоения, как и других синтаксических конструкций. Ссылка из FAQ —
[официальная документация asyncio](https://docs.python.org/3/library/asyncio.html).
