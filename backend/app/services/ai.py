import asyncio
import logging
from openai import AsyncOpenAI, APIError

from app.core.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url=getattr(settings, "OPENAI_BASE_URL", "http://travel_ollama:11434/v1"),
    api_key=settings.OPENAI_API_KEY or "ollama",
)

SYSTEM_PROMPT = (
    "Ты — точный и вежливый AI-ассистент Travel AI Platform. "
    "Твоя задача — помогать пользователям планировать путешествия и отвечать на вопросы по документам.\n\n"
    "СТРОГИЕ ПРАВИЛА ОТВЕТА:\n"
    "1. Отвечай СТРОГО НА РУССКОМ ЯЗЫКЕ.\n"
    "2. Если предоставлен контекст из документов (CONTEXT), опирайся STRICTLY на него. "
    "Не придумывай факты, названия, цифры или места, которых нет в контексте.\n"
    "3. Если ответа на вопрос нет в контексте или ты не уверен, прямо скажи: "
    "'К сожалению, в предоставленных документах нет информации об этом.'\n"
    "4. Запрещено придумывать названия парков, улиц, музеев и объектов."
)

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0


class AIServiceError(Exception):
    """Raised when the AI provider fails to return a usable response."""


def _build_system_instruction(context: str = "") -> str:
    if context:
        return f"{SYSTEM_PROMPT}\n\n=== CONTEXT FROM DOCUMENTS ===\n{context}\n=============================="
    return SYSTEM_PROMPT


async def get_ai_response(messages: list[dict], context: str = "") -> str:
    system_message = {"role": "system", "content": _build_system_instruction(context)}
    full_messages = [system_message] + messages

    for attempt in range(MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=full_messages,
                temperature=0.0,
                max_tokens=1024,
            )
            return response.choices[0].message.content

        except APIError as e:
            is_last_attempt = attempt == MAX_RETRIES - 1
            if not is_last_attempt:
                delay = BASE_DELAY_SECONDS * (2 ** attempt)
                logger.warning(f"Ollama API error, retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
                continue

            logger.error(f"Ollama API error: {e}")
            raise AIServiceError("AI service is currently unavailable.")


async def stream_ai_response(messages: list[dict], context: str = ""):
    system_message = {"role": "system", "content": _build_system_instruction(context)}
    full_messages = [system_message] + messages

    for attempt in range(MAX_RETRIES):
        try:
            stream = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=full_messages,
                temperature=0.0,
                max_tokens=1024,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return

        except APIError as e:
            is_last_attempt = attempt == MAX_RETRIES - 1
            if not is_last_attempt:
                delay = BASE_DELAY_SECONDS * (2 ** attempt)
                logger.warning(f"Ollama stream error, retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
                continue

            logger.error(f"Ollama stream error: {e}")
            raise AIServiceError("AI service is currently unavailable.")
