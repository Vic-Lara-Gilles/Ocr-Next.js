---
applyTo: "docker-compose.yml,**/Dockerfile"
---

# Docker Instructions

## Setup

Everything runs inside Docker containers. Never install on host. Only requirement: Docker + Docker Compose.

5 services on `ocr-network`: backend (FastAPI :8000), frontend (Next.js :3000), db (PostgreSQL 15 :5432), redis (Redis 7 :6379), celery (same image as backend).

## Dependency Chain

db (healthy) + redis (healthy) → backend (healthy) → frontend
db (healthy) + redis (healthy) → celery

All services use healthchecks: `pg_isready` for db, `redis-cli ping` for redis, `curl /health` for backend.

## Volumes

- `postgres_data` — named volume for PostgreSQL data
- `redis_data` — named volume for Redis data
- `./backend:/app` — bind mount for backend live reload
- `./frontend:/app` + `/app/node_modules` (anonymous) — bind mount for frontend with protected node_modules
- `ocr_uploads:/tmp/ocr_uploads` — shared between backend and celery

## Backend Dockerfile

Base: `python:3.11-slim`. System deps: `poppler-utils` (pdf2image), `libglib2.0-0` + `libgl1-mesa-glx`/`libgl1` (OpenCV), `curl` (healthcheck). Copy `requirements.txt` first → `pip install` → copy rest (layer caching). CMD: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`.

## Frontend Dockerfile

Base: `node:20-alpine`. Enable corepack for pnpm. CMD: `pnpm dev`. Source code comes via bind mount, not COPY.

## Essential Commands

```bash
# Start all services
docker compose up --build

# Apply database migrations
docker compose run --rm backend alembic upgrade head

# Create new migration
docker compose run --rm backend alembic revision --autogenerate -m "description"

# View logs
docker compose logs -f backend

# Shell access
docker compose exec backend bash
docker compose exec frontend sh

# Stop
docker compose down

# Stop and remove volumes (DESTRUCTIVE)
docker compose down -v
```
