FROM python:3.12-slim

RUN apt-get update && apt-get install -y  cmake yasm pkg-config autoconf automake libtool zlib1g-dev curl git build-essential libeigen3-dev libyaml-dev libfftw3-dev libavcodec-dev libavformat-dev libavutil-dev libswresample-dev libsamplerate0-dev libtag1-dev libchromaprint-dev python3-dev python3-numpy-dev python3-numpy python3-yaml python3-six

WORKDIR /app
COPY . .

# 3) Create your venv, install rest of Python deps
RUN pip install --no-cache-dir uv \
    && uv venv \
    && chmod +x .venv/bin/activate \
    && . .venv/bin/activate \
    && uv sync --extra platform-specific


RUN mkdir -p uploads

ENV HOST="0.0.0.0" \
    PORT="8000" \
    ENV="prod" \
    MONGO_URI="mongodb+srv://oria:....@..." \
    MONGO_DB_NAME="oriapp_db"

EXPOSE 8000

CMD ["uvicorn", "oria_backend.app:app", "--host", "0.0.0.0", "--port", "8000"]