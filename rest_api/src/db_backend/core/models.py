from django.db.models import BigIntegerField, Model


class AllowedChat(Model):
    chat_id = BigIntegerField(unique=True, primary_key=True)

    def __str__(self) -> str:
        return f"AllowedChat(chat_id={self.chat_id})"
