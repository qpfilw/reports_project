# Запуск проекта через Docker Compose

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

Если автоматическое создание администратора отключено, можно создать вручную:

```powershell
npm run make-admin
```
