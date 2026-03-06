# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=true \
    UV_PROJECT_ENVIRONMENT="/opt/venv"

WORKDIR /app

# Dependências de build (somente neste stage)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia uv do oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Instala dependências via uv (layer cacheável)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copia o projeto e instala
COPY . .
RUN uv sync --frozen

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    PYTHONUNBUFFERED=1 \
    TZ=America/Sao_Paulo \
    VIRTUAL_ENV="/opt/venv" \
    PATH="/opt/venv/bin:$PATH" \
    HOME="/app" \
    STATIC_ROOT="/staticfiles" \
    MEDIA_ROOT="/mediafiles"

# Runtime libs apenas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Cria diretórios e usuário não-root
RUN mkdir -p /app /staticfiles /mediafiles \
    && useradd -m -u 1001 appuser \
    && chown -R appuser:appuser /app /staticfiles /mediafiles

# Copia venv do builder
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
# Copia uv para o runtime (entrypoint.sh usa uv run)
COPY --from=builder /bin/uv /usr/local/bin/uv

WORKDIR /app

# Copia código (sem venv)
COPY --chown=appuser:appuser . .
COPY --chown=appuser:appuser entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Cria diretório static para evitar warning do Django
RUN mkdir -p /app/orcamento_2026/static

USER appuser

EXPOSE 8000

ENTRYPOINT ["entrypoint.sh"]
CMD ["production"]
