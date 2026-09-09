# VKBottle — рабочий конспект документации

Конспект официальной документации [vkbottle.readthedocs.io/ru/latest](https://vkbottle.readthedocs.io/ru/latest/),
собранный для этого проекта. Все примеры кода взяты дословно из документации или из
официальных примеров репозитория — ничего не придумано.

## Версии

| Что | Значение |
| --- | --- |
| Актуальный релиз vkbottle | `4.11.0` |
| Требования к Python | `>=3.10, <4.0` |
| Python в нашем venv | `3.12.9` |
| Стабильная версия VK API для LongPoll | `5.131` |

## Важное расхождение: `bot.run()` вместо `bot.run_forever()`

Сайт документации отстаёт от релиза и во многих примерах показывает `bot.run_forever()`.
В версии 4.11.0 актуальный метод — **`bot.run()`**, а `run_forever()` оставлен как
устаревший псевдоним и помечен декоратором `@deprecated` с `FutureWarning`:

```python
@deprecated(
    "Deprecated. Use run() instead",
    category=FutureWarning,
    stacklevel=0,
)
def run_forever(self) -> NoReturn:
    self.run()
```

Источник: `vkbottle/framework/base.py` (тег `v4.11.0`).

**Вывод для нашего кода:** всегда пишем `bot.run()`. Если в конспекте где-то
встречается `run_forever()` — это дословная цитата со страницы документации,
и её нужно читать как `run()`.

## Карта конспекта

| Файл | О чём |
| --- | --- |
| [01-quickstart.md](01-quickstart.md) | Установка, объект `API`, первый бот, запуск |
| [02-longpoll.md](02-longpoll.md) | **LongPoll API**: polling, параметры, `raw_event`, настройка группы |
| [03-handlers-and-rules.md](03-handlers-and-rules.md) | Хендлеры, лейблер, все встроенные правила, свои правила |
| [04-keyboards-and-attachments.md](04-keyboards-and-attachments.md) | Клавиатуры, callback-кнопки, вложения, загрузчики, карусели |
| [05-states-and-storage.md](05-states-and-storage.md) | State Dispenser, Waiter Machine, хранилища |
| [06-middlewares-and-return-managers.md](06-middlewares-and-return-managers.md) | Мидлвари и return-менеджеры |
| [07-error-handling.md](07-error-handling.md) | `VKAPIError`, `CodeException`, `ErrorHandler` |
| [08-project-structure.md](08-project-structure.md) | Разделение кода, лейблеры, мультибот, `LoopWrapper` |
| [09-api-and-tools.md](09-api-and-tools.md) | Прямые запросы, форматирование, HTTP-клиент, Callback API, логирование |
| [10-pitfalls.md](10-pitfalls.md) | Подводные камни: asyncio, блокировки, ошибки валидации |

## Токены и конфигурация

В примерах документации токен передаётся строкой (`Bot("token")`), а в официальном
примере `easy_bot.py` — через переменную окружения (`os.environ["TOKEN"]`) со ссылкой
на [12factor.net/config](https://12factor.net/config).

В нашем проекте токен берём из `.env` через `load_dotenv()`. Файл `.env` уже существует
и находится в `.gitignore`; в репозиторий кладём только `EnvExample`.
