# Scalable Microservices-Based Task Management API

A portfolio-ready task management backend built with **FastAPI, PostgreSQL, Redis, Docker Compose and microservices architecture**.

## Architecture

```text
Client
  |
  v
API Gateway :8000
  |
  +----> Task Service :8001 ----> PostgreSQL
  |
  +----> Notification Service :8002 <---- Redis
```

### Services
- **API Gateway**: single public entry point and request routing.
- **Task Service**: CRUD operations, filtering and pagination for tasks.
- **Notification Service**: consumes task events from Redis and records notification events.
- **PostgreSQL**: persistent task storage.
- **Redis**: lightweight event broker between services.

## Features
- RESTful CRUD API
- Task status and priority
- Search, filtering and pagination
- Health endpoints
- Service-to-service communication
- Redis event publishing/consuming
- PostgreSQL persistence
- Docker Compose for one-command startup
- OpenAPI/Swagger documentation

## Run locally

```bash
docker compose up --build
```

Open Swagger UI: `http://localhost:8000/docs`

Task service docs: `http://localhost:8001/docs`

## Example

Create a task:

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Build portfolio API","description":"Add microservices project to GitHub","priority":"high"}'
```

List tasks:

```bash
curl http://localhost:8000/api/tasks?page=1&page_size=10
```

## Technology Stack

Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 16, Redis 7, Docker and Docker Compose.

> This is a portfolio/learning implementation. For production deployment, add authentication/authorization, secrets management, distributed tracing, rate limiting, migrations, retries and a managed database/cache.
