import datetime
import os
from zoneinfo import ZoneInfo

from django.db import migrations


def convert_utc_to_local(apps: object, schema_editor: object) -> None:
    timezone_name = os.getenv("TIMEZONE", "UTC")
    local_tz = ZoneInfo(timezone_name)
    today = datetime.date.today()

    NotificationSubscription = apps.get_model("core", "NotificationSubscription")  # type: ignore[attr-defined]
    for sub in NotificationSubscription.objects.all():
        utc_dt = datetime.datetime.combine(today, sub.notification_time, tzinfo=datetime.timezone.utc)
        local_dt = utc_dt.astimezone(local_tz)
        sub.notification_time = local_dt.time()
        sub.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_notificationsubscription_last_seen_game_ids_and_more"),
    ]
    operations = [
        migrations.RunPython(convert_utc_to_local, reverse_code=migrations.RunPython.noop),
    ]
