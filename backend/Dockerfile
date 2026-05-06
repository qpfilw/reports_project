FROM python:3.12-slim

WORKDIR /workspace/backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /workspace/backend/requirements.txt

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /workspace/backend/requirements.txt

COPY . /workspace/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]