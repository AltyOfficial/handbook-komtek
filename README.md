# Тестовое задание

## Структура проекта

```text
api/                  URL-маршруты API
api/refbooks/         ViewSet и сериализаторы справочников
apps/refbooks/        Модели, миграции и административная панель
config/               Настройки Django и корневые URL
tests/                Тесты API и моделей
```

## Запуск

Нужны Python 3.10+ и [uv](https://docs.astral.sh/uv/).

```powershell
uv sync --group dev
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

При первом запуске задайте собственное значение `DJANGO_SECRET_KEY` в `.env`. Затем выполните:

```powershell
uv run python manage.py migrate
uv run python manage.py runserver
```

Админ-пользователя можно создать командой `uv run python manage.py createsuperuser`.

## Docker

После создания `.env` выполните:

```powershell
docker compose up --build
```

## Тесты и линтер

Добавлены автоматические тесты для API и ограничений моделей, а также линтер Ruff.

```powershell
uv run python manage.py test
uv run ruff check .
uv run ruff format --check .
```
