import os

import django

# Django must be configured before app.py is imported (which imports models at module level)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_backend.settings")
django.setup()

from api.app import app  # noqa: E402

__all__ = ["app"]
