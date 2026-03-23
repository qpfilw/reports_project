## Установка и запуск Celery / Redis 

### 1. Установи зависимости

```python -m pip install -r requirements/base.txt```

### 2. Запусти контейнер Redis в Docker

```docker compose -f ..\docker-compose.redis.yml up -d```

### 3. Запусти сервер

```uvicorn app.main:app --reload```

### 4. Запусти воркер Celery

```celery -A app.tasks.celery_app:celery_app worker --loglevel=info --pool=solo```

### 5. Проверь работу в интерфейсе Swagger


