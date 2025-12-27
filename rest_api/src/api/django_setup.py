import os
import sys
from pathlib import Path

import django


def setup_django() -> None:
    # Add the db_backend directory to Python path so Django can find its modules
    db_backend_path = Path(__file__).resolve().parent.parent / "db_backend"
    if str(db_backend_path) not in sys.path:
        sys.path.insert(0, str(db_backend_path))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_backend.settings")
    django.setup()
