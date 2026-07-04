FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock /app/backend/
RUN uv export \
    --directory /app/backend \
    --format requirements-txt \
    --no-hashes \
    --group ai-service \
    --group dev \
    --output-file /tmp/requirements-ai.txt \
    && pip install --no-cache-dir -r /tmp/requirements-ai.txt

COPY backend/ai-service /app/backend/ai-service

WORKDIR /app/backend/ai-service
