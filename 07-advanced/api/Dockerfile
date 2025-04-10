FROM python:3.10-slim-bullseye as base

# システム依存関係をインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1-dev \
    libgeos-dev \
    libgdal-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージをインストール
RUN pip3 install --no-cache-dir fastapi uvicorn[standard] psycopg2-binary rio-tiler httpx
