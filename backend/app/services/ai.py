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
        logger.error(f"Gemini API error [{e.code}]: {e.message}")
        raise AIServiceError("AI service is currently unavailable.")


async def stream_ai_response(messages: list[dict], context: str = ""):
    """
    Асинхронный генератор — отдаёт текст по кусочкам (chunk) по мере генерации.
    """
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
        async for chunk in stream:
            if chunk.text:
                yield chunk.text

    except errors.APIError as e:
        logger.error(f"Gemini API error [{e.code}]: {e.message}")
        raise AIServiceError("AI service is currently unavailable.")