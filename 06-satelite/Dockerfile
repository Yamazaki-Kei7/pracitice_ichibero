FROM python:3.10-slim-bullseye as base

# システム依存関係のインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    gdal-bin \
    python3-gdal \
    libgdal-dev \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
RUN pip3 install --no-cache-dir fastapi uvicorn[standard] rio-tiler
