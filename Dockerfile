FROM python:3.11-slim-bookworm

WORKDIR /app

# System deps (ffmpeg needed for music streaming)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -U yt-dlp kurigram

# App code
COPY . .

# Runtime dirs
RUN mkdir -p cache downloads

# Start bot
CMD ["python", "main.py"]
