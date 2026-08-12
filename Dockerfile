# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.14.6-slim AS builder

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
FROM python:3.14.6-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    PYTHONUNBUFFERED=1 \
    TZ=America/Sao_Paulo \
    VIRTUAL_ENV="/opt/venv" \
    PATH="/opt/venv/bin:$PATH" \
    HOME="/app" \
    STATIC_ROOT="/staticfiles" \
    MEDIA_ROOT="/mediafiles"

# Runtime libs apenas + ferramentas de shell
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tzdata \
    zsh \
    git \
    vim \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Cria diretórios e usuário não-root
# O diretório /app/dados será um bind mount, então as permissões serão herdadas do host
# Mas criamos aqui para garantir que exista no build
RUN mkdir -p /app /app/dados /app/dados/processados /staticfiles /mediafiles \
    && useradd -m -u 1001 appuser || true \
    && chown -R appuser:appuser /app /staticfiles /mediafiles

# Cria diretório de dados com permissões amplas para funcionar com bind mount
RUN chmod 755 /app/dados

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
RUN mkdir -p /app/orcamento/static

# Instala Starship (prompt moderno) como root
RUN curl -sS https://starship.rs/install.sh | sh -s -- -y

# Configura Zsh como shell padrão e adiciona Starship
RUN chsh -s /bin/zsh appuser

# Configurações do Zsh + Starship para o appuser
RUN mkdir -p /app/.config && \
    echo 'eval "$(starship init zsh)"' > /app/.zshrc && \
    echo 'export PATH="/opt/venv/bin:$PATH"' >> /app/.zshrc && \
    echo 'alias ll="ls -la"' >> /app/.zshrc && \
    echo 'alias py="python"' >> /app/.zshrc && \
    echo 'alias manage="python manage.py"' >> /app/.zshrc && \
    chown -R appuser:appuser /app/.zshrc /app/.config

# Configuração do Starship
COPY --chown=appuser:appuser .devcontainer/starship.toml /app/.config/starship.toml

USER appuser

ENV SHELL=/bin/zsh

EXPOSE 8000

ENTRYPOINT ["entrypoint.sh"]
CMD ["production"]
