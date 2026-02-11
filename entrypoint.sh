#!/bin/bash
set -e

# Activate the virtual environment
source /opt/venv/bin/activate

if [ "$1" = "production" ]; then
    echo "Starting in PRODUCTION mode..."
    uv run manage.py migrate --noinput && \
    uv run manage.py collectstatic --noinput && \
    uv run gunicorn orcamento_2026.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --max-requests 100 --max-requests-jitter 20
elif [ "$1" = "development" ]; then
    echo "Starting in DEVELOPMENT mode..."
    exec uv run manage.py runserver 0.0.0.0:8000
else
    echo "Unknown mode: $1"
    echo "Usage: docker run <image> [dev|prod]"
    # Fallback/Default behavior or execute command passed
    exec "$@"
fi
