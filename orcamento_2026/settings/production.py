from dj_database_url import parse as dburl
from decouple import config

from .base import *  # noqa: F403

DEBUG = False

DATABASES = {"default": config("DATABASE_URL", cast=dburl)}

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')


STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
