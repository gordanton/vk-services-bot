# 04. Клавиатуры, callback-кнопки, вложения и шаблоны

Источники: [Клавиатуры и вложения](https://vkbottle.readthedocs.io/ru/latest/tutorial/keyboards-attachments/),
[Keyboard](https://vkbottle.readthedocs.io/ru/latest/tools/keyboard/),
[MessageEvent](https://vkbottle.readthedocs.io/ru/latest/tools/message-event/),
[Uploaders](https://vkbottle.readthedocs.io/ru/latest/tools/uploaders/),
[Template](https://vkbottle.readthedocs.io/ru/latest/tools/template/).

Предполагается, что вы уже ознакомились с
[документацией ВК по клавиатурам](https://dev.vk.ru/api/bots/development/keyboard).

## Клавиатура

Импортируйте `Keyboard`, `KeyboardButtonColor` и нужные вам `action`
(например: `Text`, `OpenLink`, `Location`, `VKApps`, `Callback`).

```python
from vkbottle import Keyboard, KeyboardButtonColor, Text

keyboard = Keyboard(one_time=True, inline=False)
# О параметрах one_time и inline вы можете прочитать в документации к апи вконтакте
keyboard.add(Text("Кнопка 1"), color=KeyboardButtonColor.POSITIVE)
# Первая строка (ряд) добавляется автоматически
keyboard.row()  # Переходим на следующую строку
keyboard.add(Text("Кнопка 2"))
keyboard.add(Text("Кнопка 3", payload={"command": 3}))
```

Методы `Keyboard`:

- `add(action, color)` — добавляет кнопку к текущему ряду кнопок;
- `row()` — создаёт следующий ряд кнопок, переводит «курсор» на него;
- `get_json()` — преобразует клавиатуру в JSON-объект, который можно отправить
  в сообщении.

Отправка:

```python
await message.answer(message="Смотри сколько кнопок!!", keyboard=keyboard.get_json())
```

### Билдер-интерфейс

Тот же код в одну цепочку:

```python
from vkbottle import Keyboard, KeyboardButtonColor, Text

# ...
keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Кнопка 1"), color=KeyboardButtonColor.POSITIVE)
    .row()
    .add(Text("Кнопка 2"))
    .add(Text("Кнопка 3", payload={"command": 3}))
).get_json()

await message.answer(message="Смотри сколько кнопок!!", keyboard=keyboard)
```

### Важно: кешируйте статичную клавиатуру

Создание клавиатуры использует `json.dumps` для преобразования в JSON-объект.
Если ваша клавиатура статична, избегайте этой повторяющейся операции: создайте её
один раз и используйте уже «преобразованную» клавиатуру.

Так сделано в официальном примере `easy_bot.py`:

```python
KEYBOARD = Keyboard(one_time=True).add(Text("Съесть еще", {"cmd": "eat"})).get_json()
```

### Удаление клавиатуры

Чтобы удалить клавиатуру у пользователя, нужно отправить `EMPTY_KEYBOARD`.

## Callback-кнопки: `MessageEvent`

Обработка callback-кнопок делается через сырое событие `MESSAGE_EVENT` с готовым
dataclass `MessageEvent`:

```python
from vkbottle import GroupEventType
from vkbottle.bot import MessageEvent

@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def handle_message_event(event: MessageEvent):
    await event.show_snackbar("Сейчас я исчезну")
```

Преимущества этого объекта по документации:

- Никакого `object` — всё находится уже в `event`, вместе с `group_id`.
- Поддержка всех генераторов event-data при помощи соответствующих функций.
- Поддержка рулзов, связанных с payload.
- Так же есть `message_edit` и `message_send`.

### Старый способ (для понимания, что происходит под капотом)

```python
from vkbottle import GroupEventType, GroupTypes, ShowSnackbarEvent

@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=GroupTypes.MessageEvent)
async def handle_message_event(event: GroupTypes.MessageEvent):
    await event.ctx_api.messages.send_message_event_answer(
        event_id=event.object.event_id,
        user_id=event.object.user_id,
        peer_id=event.object.peer_id,
        event_data=ShowSnackbarEvent(text="Сейчас я исчезну").model_dump_json(),
    )
```

## Вложения

### Если ссылка на вложение уже есть

Если у вас есть строка вида `"type{OWNER_ID}_{ITEM_ID}"`
(например `"photo-41629685_457239401"`), отправляйте так:

```python
attachment = ...  # see example above

@bot.on.message
async def send_attachment(message):
    await message.answer("See that attachment!", attachment=attachment)
```

### Если вложение загружается динамически

```python
uploader = AnyUploader(bot.api)  # see uploaders types in "Uploaders documentation" above

@bot.on.message()
async def send_attachment(message):
    attachment = await uploader.upload("path/to/file")
    await message.answer("See that attachment!", attachment=attachment)
```

## Загрузчики (Uploaders)

Загрузка медиа разного типа в ВК. Аплоадер принимает объект API при инициализации.

```python
from vkbottle import PhotoMessageUploader
from vkbottle.bot import Bot

bot = Bot("token")
photo_uploader = PhotoMessageUploader(bot.api)

@bot.on.message(text="photo")
async def handler(message):
    photo = await photo_uploader.upload(
        file_source="photo.png",
        peer_id=m.peer_id,
    )
    await message.answer(attachment=photo)

bot.run()
```

> ⚠️ В этом примере из документации опечатка: аргумент хендлера называется `message`,
> а внутри используется `m.peer_id`. У нас должно быть `message.peer_id`.

### Интерфейс аплоадера

Два основных метода с одинаковым интерфейсом:

- `.upload(...)` — возвращает готовую строку аттачмента;
- `.raw_upload(...)` — возвращает словарь с ответом сервера.

Не все аплоадеры имеют метод `upload` — для них невозможно вернуть строку аттачмента.
Обычно нужен только `upload`.

Все аплоадеры различаются методом получения сервера: `.get_server(...)`.

Методы базового класса, одинаковые для всех:

- `.upload_files(url, files)` — загрузка файлов методом POST;
- `.get_bytes_io(data)` — приводит сырые байты в подходящий для ВК вид;
- `.generate_attachment_string(attachment_type, owner_id, item_id, access_key)` —
  делает строку, которую ВК принимает как медиа для отправки;
- `.read(file_source)` — читает файл, если `file_source` строка, а если байты —
  возвращает их.

### Виды аплоадеров

**Фото:**

| Класс | Назначение |
| --- | --- |
| `PhotoMessageUploader` | загрузка в сообщение |
| `PhotoToAlbumUploader` | загрузка в альбом |
| `PhotoWallUploader` | загрузка на стену |
| `PhotoFaviconUploader` | загрузка аватарки |
| `PhotoChatFaviconUploader` | загрузка аватарки беседы |
| `PhotoMarketUploader` | загрузка картинки для товара |

**Документы:**

| Класс | Назначение |
| --- | --- |
| `DocWallUploader` | загрузка документов на стену |
| `DocMessagesUploader` | загрузка документов в сообщение |
| `VoiceMessageUploader` | загрузка голосовых сообщений |
| `GraffitiUploader` | загрузка граффити |

**Прочее:** `AudioUploader` (аудио), `VideoUploader` (видео).

Есть также тип `speech` — загрузка аудиофайлов для распознавания речи.

## Шаблоны (карусель)

На данный момент ВКонтакте поддерживает только один вид шаблона — карусель.

```python
from vkbottle import TemplateElement, template_gen

my_template = template_gen(
    TemplateElement(...), # о том как нужно сочетать параметры можно
    TemplateElement(...)  # прочитать в документации Вконтакте выше
)

# my_template - готовый для отправки json
# ...
await message.answer("Держи карусель!", template=my_template)
```

`TemplateElement` — элемент шаблона; названия полей соответствуют названиям полей
в документации ВКонтакте. `template_gen` создаёт шаблон из предоставленных элементов.
В туториале `template_gen` и `TemplateElement` импортируются из `vkbottle.tools`,
а в разделе Tools — из `vkbottle`; работают оба варианта.
