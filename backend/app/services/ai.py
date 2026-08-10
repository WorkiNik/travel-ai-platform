import asyncio
import logging

from openai import AsyncOpenAI, APIError, RateLimitError

from app.core.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url="http://ollama:11434/v1",
    api_key="ollama",  # Ollama не проверяет ключ, но клиенту openai он нужен формально
)

SYSTEM_PROMPT = (
    "You are a helpful travel assistant embedded in the Travel AI Platform. "
    "You help users plan trips, suggest itineraries, recommend destinations, "
    "and answer travel-related questions. Keep responses concise and practical. "
    "If a question is unrelated to travel, politely redirect the conversation."
)

RETRYABLE_EXCEPTIONS = (RateLimitError,)
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.5


class AIServiceError(Exception):
    """Raised when the AI provider fails to return a usable response."""


def _to_openai_messages(messages: list[dict], context: str = "") -> list[dict]:
    system = SYSTEM_PROMPT + (f"\n\n{context}" if context else "")
    return [{"role": "system", "content": system}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]


async def get_ai_response(messages: list[dict], context: str = "") -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=_to_openai_messages(messages, context),
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content

        except RETRYABLE_EXCEPTIONS as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Ollama error after retries: {e}")
                raise AIServiceError("AI service is currently unavailable.")
            delay = BASE_DELAY_SECONDS * (2 ** attempt)
            logger.warning(f"Retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s")
            await asyncio.sleep(delay)

        except APIError as e:
            logger.error(f"Ollama API error: {e}")
            raise AIServiceError("AI service is currently unavailable.")


async def stream_ai_response(messages: list[dict], context: str = ""):
    try:
        stream = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=_to_openai_messages(messages, context),
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    except APIError as e:
        logger.error(f"Ollama streaming error: {e}")
        raise AIServiceError("AI service is currently unavailable.")