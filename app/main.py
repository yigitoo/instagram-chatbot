import logging
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, Query, Request, Response

from app.config import settings
from app.webhook_handler import handle_webhook

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    yield
    await app.state.http_client.aclose()


app = FastAPI(title="Instagram DM Chatbot", lifespan=lifespan)


@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode", default=""),
    token: str = Query(alias="hub.verify_token", default=""),
    challenge: str = Query(alias="hub.challenge", default=""),
):
    if mode == "subscribe" and token == settings.meta_verify_token:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    payload: dict[str, Any] = await request.json()
    client: httpx.AsyncClient = request.app.state.http_client
    background_tasks.add_task(handle_webhook, payload, client)
    return Response(status_code=200)


@app.get("/health")
async def health():
    return {"status": "ok"}
