import logging
from typing import Any

import httpx

from app import gemini, instagram, pause_manager

logger = logging.getLogger(__name__)


async def handle_webhook(payload: dict[str, Any], client: httpx.AsyncClient) -> None:
    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            await _process_event(event, client)


async def _process_event(event: dict[str, Any], client: httpx.AsyncClient) -> None:
    message = event.get("message")
    if message is None:
        return

    sender_id = event.get("sender", {}).get("id")
    recipient_id = event.get("recipient", {}).get("id")
    if not sender_id or not recipient_id:
        return

    # Echo handling: messages sent FROM the page
    if message.get("is_echo"):
        if not message.get("app_id"):
            # Admin replied manually — pause bot for this conversation
            logger.info("Admin replied to %s, pausing bot", recipient_id)
            pause_manager.pause(recipient_id)
        # Skip all echoes (both admin and bot)
        return

    # Only handle text messages
    text = message.get("text")
    if not text:
        return

    # Check if conversation is paused
    if pause_manager.is_paused(sender_id):
        logger.debug("Conversation with %s is paused, skipping", sender_id)
        return

    # Generate and send reply
    try:
        reply = await gemini.generate_reply(text)
        await instagram.send_message(sender_id, reply, client)
    except Exception:
        logger.exception("Error processing message from %s", sender_id)
