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

# ── Cloudflare Tunnel: proxy headers e CSRF ─────────────────────────────────
# Cloudflared passa requisições como HTTP local → Django precisa confiar no SSL do Cloudflare
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
CSRF_TRUSTED_ORIGINS = [
    'https://orcamento.elijunior.click',
]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
