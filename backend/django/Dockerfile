FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/uv.lock /app/backend/
RUN uv export \
    --directory /app/backend \
    --format requirements-txt \
    --no-hashes \
    --group django \
    --group dev \
    --output-file /tmp/requirements-django.txt \
    && pip install --no-cache-dir -r /tmp/requirements-django.txt

COPY backend/django /app/backend/django

WORKDIR /app/backend/django
