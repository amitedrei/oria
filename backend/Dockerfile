FROM --platform=linux/amd64 python:3.10-slim


RUN apt-get update && apt-get install -y \
    build-essential \
    libyaml-dev \
    libfftw3-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    python3-dev \
    python3-numpy-dev \
    python3-yaml \
    git \
    wget \
    pkg-config

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir uv \
    && uv venv \
    && uv sync


RUN mkdir -p uploads

ENV HOST="0.0.0.0" \
    PORT="8000" \
    ENV="prod" \
    MONGO_URI="mongodb+srv://oria:AydZmQPhhle2GDGF@oriapp.vsmdghw.mongodb.net" \
    MONGO_DB_NAME="oriapp_db"

EXPOSE 8000

CMD ["./.venv/bin/uvicorn", "oria_backend.app:app", "--host", "0.0.0.0", "--port", "8000"]