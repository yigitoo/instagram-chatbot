import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_message(recipient_id: str, text: str, client: httpx.AsyncClient) -> None:
    url = f"https://graph.instagram.com/v21.0/{settings.instagram_account_id}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }
    headers = {
        "Authorization": f"Bearer {settings.meta_page_access_token}",
        "Content-Type": "application/json",
    }
    response = await client.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        logger.error("Failed to send message: %s %s", response.status_code, response.text)
    else:
        logger.info("Message sent to %s", recipient_id)
