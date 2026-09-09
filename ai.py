"""Обёртка над ProxyAPI: генерация ответов и память диалогов.

ProxyAPI совместим с официальным SDK openai — меняются только базовый адрес и ключ.
Документация: https://proxyapi.ru/docs/openai-text-generation
"""

from collections import defaultdict, deque

from openai import AsyncOpenAI, OpenAIError
from vkbottle.modules import logger

from config import (
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_SYSTEM_PROMPT,
    AI_TEMPERATURE,
    AI_TIMEOUT,
    HISTORY_LIMIT,
    PROXYAPI_BASE_URL,
    PROXYAPI_KEY,
)

client = AsyncOpenAI(
    api_key=PROXYAPI_KEY,
    base_url=PROXYAPI_BASE_URL,
    timeout=AI_TIMEOUT,
)

# Модель не помнит переписку: историю нужно отправлять заново при каждом запросе.
# Держим по HISTORY_LIMIT пар "вопрос-ответ" на каждый диалог (peer_id).
_history: dict[int, deque[dict[str, str]]] = defaultdict(
    lambda: deque(maxlen=HISTORY_LIMIT * 2),
)


class AIError(Exception):
    """Не удалось получить ответ от модели."""


def reset_history(peer_id: int) -> None:
    _history.pop(peer_id, None)


async def ask(peer_id: int, question: str) -> str:
    """Отправляет вопрос модели с учётом истории диалога и возвращает ответ."""
    history = _history[peer_id]
    messages = [
        {"role": "system", "content": AI_SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": question},
    ]

    try:
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
        )
    except OpenAIError as e:
        logger.error("Запрос к ProxyAPI не удался: {}", e)
        raise AIError(str(e)) from e

    choice = response.choices[0]
    answer = (choice.message.content or "").strip()

    if not answer:
        logger.warning("ProxyAPI вернул пустой ответ, finish_reason={}", choice.finish_reason)
        raise AIError("пустой ответ модели")

    if choice.finish_reason == "length":
        answer += "…"

    if response.usage is not None:
        logger.debug(
            "Диалог {}: потрачено токенов {} (запрос {}, ответ {})",
            peer_id,
            response.usage.total_tokens,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    return answer


async def close() -> None:
    await client.close()
