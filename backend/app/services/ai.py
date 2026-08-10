import asyncio
import logging

from google import genai
from google.genai import types, errors

from app.core.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "You are a helpful travel assistant embedded in the Travel AI Platform. "
    "You help users plan trips, suggest itineraries, recommend destinations, "
    "and answer travel-related questions. Keep responses concise and practical. "
    "If a question is unrelated to travel, politely redirect the conversation."
)

# Коды ошибок, при которых имеет смысл повторить запрос — временная перегрузка/лимиты,
# а не наша ошибка (400 и подобные повторять бессмысленно — они не самоисправятся)
RETRYABLE_CODES = {429, 503}
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.5


class AIServiceError(Exception):
    """Raised when the AI provider fails to return a usable response."""


def _to_gemini_contents(messages: list[dict]) -> list[dict]:
    role_map = {"user": "user", "assistant": "model"}
    return [
        {"role": role_map.get(m["role"], "user"), "parts": [{"text": m["content"]}]}
        for m in messages
    ]


def _build_system_instruction(context: str = "") -> str:
    if context:
        return f"{SYSTEM_PROMPT}\n\n{context}"
    return SYSTEM_PROMPT


async def get_ai_response(messages: list[dict], context: str = "") -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.aio.models.generate_content(
                model=settings.OPENAI_MODEL,
                contents=_to_gemini_contents(messages),
                config=types.GenerateContentConfig(
                    system_instruction=_build_system_instruction(context),
                    temperature=0.7,
                    max_output_tokens=1024,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            return response.text

        except errors.APIError as e:
            is_retryable = e.code in RETRYABLE_CODES
            is_last_attempt = attempt == MAX_RETRIES - 1

            if is_retryable and not is_last_attempt:
                delay = BASE_DELAY_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Gemini {e.code}, retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                continue

            logger.error(f"Gemini API error [{e.code}]: {e.message}")
            raise AIServiceError("AI service is currently unavailable.")


async def stream_ai_response(messages: list[dict], context: str = ""):
    """
    Retry применяется только к открытию стрима (до того как пошли первые токены) —
    если сбой случится уже в процессе стриминга, чисто "перезапустить" на полпути
    нельзя, не запутав клиента дублями текста.
    """
    stream = None

    for attempt in range(MAX_RETRIES):
        try:
            stream = await client.aio.models.generate_content_stream(
                model=settings.OPENAI_MODEL,
                contents=_to_gemini_contents(messages),
                config=types.GenerateContentConfig(
                    system_instruction=_build_system_instruction(context),
                    temperature=0.7,
                    max_output_tokens=1024,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            break

        except errors.APIError as e:
            is_retryable = e.code in RETRYABLE_CODES
            is_last_attempt = attempt == MAX_RETRIES - 1

            if is_retryable and not is_last_attempt:
                delay = BASE_DELAY_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Gemini {e.code}, retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                continue

            logger.error(f"Gemini API error [{e.code}]: {e.message}")
            raise AIServiceError("AI service is currently unavailable.")

    try:
        async for chunk in stream:
            if chunk.text:
                yield chunk.text
    except errors.APIError as e:
        logger.error(f"Gemini API error during streaming [{e.code}]: {e.message}")
        raise AIServiceError("AI service is currently unavailable.")