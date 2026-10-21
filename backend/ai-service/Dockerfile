# syntax=docker/dockerfile:1
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

# Model-runtime wheels are large. Keep completed downloads across failed builds
# and allow slow links more than pip's default 15-second socket timeout.
ARG PIP_DEFAULT_TIMEOUT=120
ARG PIP_RETRIES=5
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    uv export \
    --directory /app/backend \
    --format requirements-txt \
    --no-hashes \
    --group ai-service \
    --group dev \
    --output-file /tmp/requirements-ai.txt \
    && pip install --timeout "$PIP_DEFAULT_TIMEOUT" --retries "$PIP_RETRIES" --no-deps -r /tmp/requirements-ai.txt \
    && pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python opencv-contrib-python-headless \
    && pip install --timeout "$PIP_DEFAULT_TIMEOUT" --retries "$PIP_RETRIES" --no-deps opencv-contrib-python==5.0.0.93 \
    && python /app/backend/shared/opencv_runtime.py \
    && PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True python -c \
        "from paddlex.utils.deps import require_extra; require_extra('ocr-core'); from paddlex.inference.common.reader.image_reader import ReadImage; ReadImage(format='RGB')"

COPY backend/ai-service /app/backend/ai-service
COPY scripts/fetch_face_models.py /app/scripts/fetch_face_models.py

WORKDIR /app/backend/ai-service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
