FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
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

COPY backend/shared /app/backend/shared
COPY backend/django /app/backend/django
COPY docs/openapi/identitycore-public-api.yaml /app/docs/openapi/identitycore-public-api.yaml

WORKDIR /app/backend/django

# The Postman integration executes the checked-in JavaScript response scripts.
# Keep its interpreter and collection fixtures in the test target only.
FROM runtime AS test
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*
COPY postman /app/postman

FROM runtime AS production
