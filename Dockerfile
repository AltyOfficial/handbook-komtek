FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY manage.py ./
COPY api ./api
COPY apps ./apps
COPY config ./config

EXPOSE 8000

CMD ["sh", "-c", "uv run --no-sync python manage.py migrate && exec uv run --no-sync python manage.py runserver 0.0.0.0:8000"]
