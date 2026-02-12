from typing import ClassVar

from django.db.models import CASCADE, BigIntegerField, Index, Model, OneToOneField, Q
from django.db.models.fields import BooleanField, CharField, DateTimeField, TimeField


class AllowedChat(Model):
    chat_id = BigIntegerField(unique=True, primary_key=True)
    name = CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"AllowedChat(chat_id={self.chat_id}, name='{self.name}')"


class NotificationSubscription(Model):
    chat = OneToOneField(AllowedChat, on_delete=CASCADE, null=False)
    chat_id: int  # Type hint for auto-generated FK field
    notification_time = TimeField(null=False)
    enabled = BooleanField(default=True, null=False)

    class Meta:
        indexes: ClassVar[list[Index]] = [
            Index(
                fields=["notification_time", "enabled"],
                name="notif_time_enabled_true_idx",
                condition=Q(enabled=True),
            ),
        ]

    def __str__(self) -> str:
        return f"NotificationSubscription(chat_id={self.chat_id}, notification_time={self.notification_time})"


class Job(Model):
    name = CharField(max_length=255, unique=True, primary_key=True)
    last_run = DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Job(name={self.name}, last_run={self.last_run})"
