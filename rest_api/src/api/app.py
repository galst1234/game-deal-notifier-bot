from asgiref.sync import sync_to_async
from fastapi import FastAPI
from pydantic import BaseModel

from api.django_setup import setup_django
from api.isthereanydeal.deals_list import DealItem
from api.isthereanydeal.giveaways import get_current_giveaways

setup_django()

from core.models import AllowedChat  # noqa


def _check_chat_exists(chat_id: int) -> bool:
    """Helper function to check if chat exists (must be called from sync context)."""
    return AllowedChat.objects.filter(chat_id=chat_id).exists()


app = FastAPI()


@app.get("/")
async def hello_world() -> dict:
    return {"message": "Hello World"}


@app.get("/api/v1/isthereanydeal/current-giveaways")
async def current_giveaways() -> list[DealItem]:
    return await sync_to_async(get_current_giveaways)()


class AllowedChatResponse(BaseModel):
    chat_id: int
    is_allowed: bool


@app.get("/api/v1/allowed-chats/{chat_id}")
async def check_allowed_chat(chat_id: int) -> AllowedChatResponse:
    is_allowed = await sync_to_async(_check_chat_exists, thread_sensitive=False)(
        chat_id,
    )
    return AllowedChatResponse(chat_id=chat_id, is_allowed=is_allowed)
