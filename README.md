# Запуск проекта через Docker Compose

Файлы из этого архива нужно распаковать в корень проекта `reports_project` с заменой существующих файлов.

## Первый запуск

```powershell
npm run dev
```

или без npm-скрипта:

```powershell
docker compose up --build
```

После запуска будут доступны:

- frontend: http://localhost:5173
- backend: http://localhost:8000
- Swagger/OpenAPI: http://localhost:8000/docs
- healthcheck API: http://localhost:8000/api/v1/health
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Остановка

```powershell
npm run stop
```

## Полный сброс данных PostgreSQL/Redis/storage

```powershell
npm run reset
```

После `reset` база будет создана заново при следующем `npm run dev`.

## Создание администратора

Если автоматическое создание администратора отключено, создай его вручную:

```powershell
npm run make-admin
```

## Что делает Compose

- поднимает PostgreSQL;
- поднимает Redis;
- запускает миграции Alembic;
- выполняет начальную инициализацию ролей через `python -m app.db.init_db`;
- запускает FastAPI через Uvicorn;
- запускает Celery worker;
- запускает React/Vite frontend.

## Важная правка

В архиве также есть исправленный `backend/app/core/config.py`: alias для JWT-секретов заменены на `JWT_SECRET_KEY` и `JWT_REFRESH_SECRET_KEY`. Без этой правки переменные окружения из Compose и `.env` могут не подхватываться корректно.
