# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.10-slim

RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-numpy-dev \
    python3-yaml \
    git \
    wget \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/app/.uv-cache \
    uv venv && uv sync

COPY . .

RUN mkdir -p uploads

ENV HOST="0.0.0.0" \
    PORT="8000" \
    ENV="prod" \
    MONGO_URI="mongodb+srv://oria:AydZmQPhhle2GDGF@oriapp.vsmdghw.mongodb.net" \
    MONGO_DB_NAME="oriapp_db" \
    UV_CACHE_DIR="/app/.uv-cache"

EXPOSE 8000

CMD ["./.venv/bin/uvicorn", "oria_backend.app:app", "--host", "0.0.0.0", "--port", "8000"]