# VK-бот услуг

Бот сообщества ВКонтакте: меню услуг, заявки, отзывы и ответы через ProxyAPI.
Работает на LongPoll (`vkbottle`), входящие порты не нужны.

## Локальный запуск

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Скопируйте `EnvExample` в `.env` и заполните ключи. Затем:

```bash
python bot.py
```

## Docker

```bash
docker compose up -d --build
docker compose logs -f
```

`.env` остаётся на хосте и не попадает в образ. Заявки пишутся в том `bot-data`.

## Деплой на сервер

1. Остановите локальный бот — два LongPoll на один токен дают двойные ответы.
2. Скопируйте проект на сервер (без `venv/` и `.env`).
3. Создайте `.env` из `EnvExample` уже на сервере.
4. Запустите `docker compose up -d --build`.

Ссылка на диалог сообщества: `https://vk.me/club241328056`.
