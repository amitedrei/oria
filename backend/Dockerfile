FROM python:3.12-slim

WORKDIR /app

RUN apt update && apt install -y \
    curl \
    cmake \
    make \
    g++ \
    git \
    python3-dev \
    python3-pip \
    libfftw3-dev \
    libsamplerate0-dev \
    libeigen3-dev \
    libyaml-dev \
    libtag1-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    build-essential \
    cython3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY . .

RUN pip install --no-cache-dir uv && \
    uv venv && chmod +x .venv/bin/activate && .venv/bin/activate && \
    uv sync --extra platform-specific


RUN mkdir -p uploads

ENV HOST="0.0.0.0"
ENV PORT=8000
ENV ENV="prod"
ENV MONGO_URI="mongodb+srv://oria:AydZmQPhhle2GDGF@oriapp.vsmdghw.mongodb.net"
ENV MONGO_DB_NAME="oriapp_db"

EXPOSE 8000

CMD [".venv/bin/python", "-m", "uvicorn", "oria_backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
