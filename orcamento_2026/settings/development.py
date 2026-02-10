from dj_database_url import parse as dburl
from decouple import config
from pathlib import Path

from .base import *  # noqa: F403


INSTALLED_APPS += [  # noqa: F405
    # Development tools
    "django_extensions",
    "debug_toolbar",
]

DIR = BASE_DIR  # noqa: F405

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

default_dburl = f"sqlite:///{Path.joinpath(DIR, '../db.sqlite3').resolve()}"
DATABASES = {"default": config("DATABASE_URL", default=default_dburl, cast=dburl)}

TEMPLATES[0]["OPTIONS"]["context_processors"].insert(0, "django.template.context_processors.debug")

# For Django Debug Toolbar
INTERNAL_IPS = ["127.0.0.1"]