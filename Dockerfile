# Use ubi10-minimal as the base image
FROM registry.access.redhat.com/ubi10/ubi-minimal:latest

# Install tzdata
RUN microdnf install -y tzdata \
    && microdnf clean all

# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=true \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    UV_CACHE_DIR="/uv_cache" \
    XDG_DATA_HOME="/uv_data" \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV="/opt/venv" \
    PATH="/opt/venv/bin:$PATH" \
    start="dev" \
    HOME="/app" \
    STATIC_ROOT="/staticfiles" \
    MEDIA_ROOT="/mediafiles"

WORKDIR /app

# Ensure 1001 can write to workdir and cache/data dirs
RUN mkdir -p /app /uv_cache /uv_data /opt/venv /staticfiles /mediafiles \
    && chown -R 1001:1001 /app /uv_cache /uv_data /opt/venv /staticfiles /mediafiles

# Switch to user 1001 for all subsequent operations
USER 1001

# Install Python and dependencies
# Copy only files needed for installation first
COPY --chown=1001:1001 pyproject.toml uv.lock ./
COPY --chown=1001:1001 entrypoint.sh /usr/local/bin/entrypoint.sh

# Ensure entrypoint is executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy the rest of the application
COPY --chown=1001:1001 . .

# Install the project itself
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["entrypoint.sh"]

# Default command
CMD ["development"]
