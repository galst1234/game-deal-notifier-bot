import datetime
from enum import StrEnum
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import Q
from fastapi import FastAPI, Response
from pydantic import BaseModel

from api.isthereanydeal.deals_list import DealItem
from api.isthereanydeal.giveaways import get_current_giveaways
from core.models import Chat, Job, NotificationSubscription

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


def _is_chat_allowed(chat_id: int) -> bool:
    return Chat.objects.filter(chat_id=chat_id, status=Chat.Status.APPROVED).exists()


@app.get("/api/v1/allowed-chats/{chat_id}")
async def check_allowed_chat(chat_id: int) -> AllowedChatResponse:
    is_allowed = await sync_to_async(_is_chat_allowed, thread_sensitive=False)(
        chat_id,
    )
    return AllowedChatResponse(chat_id=chat_id, is_allowed=is_allowed)


class SubscriptionType(StrEnum):
    ALL = "all"
    NEW_NOTIFY_EMPTY = "new_notify_empty"
    NEW_SILENT_EMPTY = "new_silent_empty"


class SubscriptionRequest(BaseModel):
    chat_id: int
    time: datetime.time
    subscription_type: SubscriptionType = SubscriptionType.NEW_NOTIFY_EMPTY


@app.post("/api/v1/subscriptions")
async def subscribe_chat(body: SubscriptionRequest) -> Response:
    _, created = await sync_to_async(
        lambda: NotificationSubscription.objects.update_or_create(
            chat_id=body.chat_id,
            defaults={
                "notification_time": body.time,
                "enabled": True,
                "subscription_type": body.subscription_type.value,
                "last_seen_game_ids": [],
            },
        ),
    )()
    return Response(status_code=201 if created else 204)


@app.delete("/api/v1/subscriptions/{chat_id}")
async def unsubscribe_chat(chat_id: int) -> Response:
    updated = await sync_to_async(
        lambda: NotificationSubscription.objects.filter(chat_id=chat_id, enabled=True).update(enabled=False),
    )()
    return Response(status_code=204 if updated else 404)


class PendingNotification(BaseModel):
    chat_id: int
    deals: list[DealItem]


def _get_pending_subscriptions() -> list[NotificationSubscription]:
    with transaction.atomic():
        job, _ = Job.objects.get_or_create(name="subscriptions_job")
        last_run = job.last_run
        now = datetime.datetime.now(tz=datetime.UTC)

        pending_subscriptions = []
        if last_run.date() == now.date():
            if last_run.time() <= now.time():
                # Same day case: notification times between last_run and now
                pending_subscriptions = list(
                    NotificationSubscription.objects.filter(
                        notification_time__gt=last_run.time(),
                        notification_time__lte=now.time(),
                        enabled=True,
                    ),
                )
        elif now.date() - last_run.date() == datetime.timedelta(days=1):
            # Day wrap-around: notification times after last_run OR before now
            pending_subscriptions = list(
                NotificationSubscription.objects.filter(enabled=True).filter(
                    Q(notification_time__gt=last_run.time()) | Q(notification_time__lte=now.time()),
                ),
            )
        else:
            # More than 1 day gap, consider all notifications pending
            pending_subscriptions = list(NotificationSubscription.objects.filter(enabled=True))

        job.last_run = now
        job.save()
    return pending_subscriptions


def _build_pending_notifications(subscriptions: list[NotificationSubscription]) -> list[PendingNotification]:
    giveaways = get_current_giveaways()
    current_game_ids: list[UUID] = [deal.id for deal in giveaways]

    notifications: list[PendingNotification] = []
    for subscription in subscriptions:
        if subscription.subscription_type == NotificationSubscription.SubscriptionType.ALL:
            notifications.append(PendingNotification(chat_id=subscription.chat_id, deals=giveaways))
        else:
            last_seen: set[UUID] = set(subscription.last_seen_game_ids)
            new_deals = [deal for deal in giveaways if deal.id not in last_seen]
            if (
                new_deals
                or subscription.subscription_type == NotificationSubscription.SubscriptionType.NEW_NOTIFY_EMPTY
            ):
                notifications.append(PendingNotification(chat_id=subscription.chat_id, deals=new_deals))

    sub_ids = [sub.pk for sub in subscriptions]
    NotificationSubscription.objects.filter(pk__in=sub_ids).update(last_seen_game_ids=current_game_ids)

    return notifications


def _get_pending_notifications() -> list[PendingNotification]:
    subscriptions = _get_pending_subscriptions()
    if not subscriptions:
        return []
    return _build_pending_notifications(subscriptions)


@app.get("/api/v1/notifications/pending")
async def get_pending_notifications() -> list[PendingNotification]:
    return await sync_to_async(_get_pending_notifications)()
