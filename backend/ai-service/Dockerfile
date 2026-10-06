FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libsm6 \
        libxext6 \
        libxrender1 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/uv.lock /app/backend/
COPY backend/shared /app/backend/shared

RUN uv export \
    --directory /app/backend \
    --format requirements-txt \
    --no-hashes \
    --group ai-service \
    --group dev \
    --output-file /tmp/requirements-ai.txt \
    && pip install --no-cache-dir --no-deps -r /tmp/requirements-ai.txt \
    && pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python opencv-contrib-python-headless \
    && pip install --no-cache-dir --no-deps opencv-contrib-python-headless==5.0.0.93 \
    && python /app/backend/shared/opencv_runtime.py

COPY backend/ai-service /app/backend/ai-service

WORKDIR /app/backend/ai-service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
