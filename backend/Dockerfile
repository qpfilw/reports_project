FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
COPY requirements/dev.txt requirements/dev.txt

RUN python -m pip install --upgrade pip \
    && pip install -r requirements/base.txt -r requirements/dev.txt

COPY . .

EXPOSE 8000
