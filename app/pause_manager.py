import time

from app.config import settings

_paused_conversations: dict[str, float] = {}


def pause(conversation_id: str) -> None:
    expiry = time.time() + settings.admin_pause_duration_minutes * 60
    _paused_conversations[conversation_id] = expiry


def is_paused(conversation_id: str) -> bool:
    expiry = _paused_conversations.get(conversation_id)
    if expiry is None:
        return False
    if time.time() >= expiry:
        _paused_conversations.pop(conversation_id, None)
        return False
    return True


def resume(conversation_id: str) -> None:
    _paused_conversations.pop(conversation_id, None)
