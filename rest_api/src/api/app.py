import datetime

import pytz
from asgiref.sync import sync_to_async
from django.db.models import Q
from fastapi import FastAPI, Response
from pydantic import BaseModel

from api.django_setup import setup_django
from api.isthereanydeal.deals_list import DealItem
from api.isthereanydeal.giveaways import get_current_giveaways
from config import TIMEZONE

setup_django()

from django.db import transaction  # noqa
from core.models import AllowedChat, NotificationSubscription, Job  # noqa


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


class SubscriptionRequest(BaseModel):
    chat_id: int
    time: datetime.time


@app.post("/api/v1/subscriptions")
async def subscribe_chat(body: SubscriptionRequest) -> Response:
    _, created = await sync_to_async(
        lambda: NotificationSubscription.objects.update_or_create(
            chat_id=body.chat_id,
            defaults={"notification_time": body.time, "enabled": True},
        ),
    )()
    return Response(status_code=201 if created else 204)


@app.delete("/api/v1/subscriptions/{chat_id}")
async def unsubscribe_chat(chat_id: int) -> Response:
    updated = await sync_to_async(
        lambda: NotificationSubscription.objects.filter(chat_id=chat_id, enabled=True).update(enabled=False),
    )()
    return Response(status_code=204 if updated else 404)


def _get_pending_subscriptions() -> list[int]:
    with transaction.atomic():
        job, _ = Job.objects.get_or_create(name="subscriptions_job")
        last_run = job.last_run
        now = datetime.datetime.now(tz=pytz.timezone(TIMEZONE))
        if last_run <= now:
            pending_subscriptions = NotificationSubscription.objects.filter(
                notification_time__gt=last_run.astimezone(pytz.timezone(TIMEZONE)).time(),
                notification_time__lte=now.time(),
                enabled=True,
            ).values_list("chat_id", flat=True)
        else:
            # Handle day wrap-around
            pending_subscriptions = (
                NotificationSubscription.objects
                .filter(enabled=True)
                .filter(Q(notification_time__gt=last_run.time()) | Q(notification_time__lte=now.time()))
                .values_list("chat_id", flat=True)
            )
        job.last_run = now
        job.save()
    return list(pending_subscriptions)


@app.get("/api/v1/notifications/pending")
async def get_pending_notifications() -> list[int]:
    return await sync_to_async(_get_pending_subscriptions)()
