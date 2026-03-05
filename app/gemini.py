import asyncio

from google import genai

from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

SYSTEM_INSTRUCTION = (
    "You are a helpful Instagram DM assistant. "
    "Keep your responses concise and friendly. "
    "Respond in the same language the user writes in."
)


async def generate_reply(user_message: str) -> str:
    response = await asyncio.to_thread(
        _client.models.generate_content,
        model=settings.gemini_model,
        contents=user_message,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )
    return response.text
