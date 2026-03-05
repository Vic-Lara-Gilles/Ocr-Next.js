# OCR Platform

Document OCR system that extracts text, tables, and structured data from PDFs using Google Gemini 2.0 Flash. Small PDFs (< 5 pages) processed synchronously; larger PDFs dispatched to Celery worker asynchronously.

## Architecture

5 Docker services on `ocr-network`: FastAPI backend (:8000), Next.js 16 frontend (:3000), PostgreSQL 15 (:5432), Redis 7 (:6379), Celery worker. Dependencies: db + redis → backend → frontend; db + redis → celery.

Backend follows layered architecture: Routes → Services → Repositories → Models → Database. Frontend uses: Pages → Components → Hooks → Services → Types.

## Folder Structure

- `backend/main.py` — FastAPI app, CORS, routers, `/health`
- `backend/app/` — config.py, database.py, models/, schemas/, repositories/, services/, routes/, tasks/
- `backend/alembic/` — Database migrations (autogenerate)
- `frontend/src/app/` — App Router pages (landing, dashboard, results/[id])
- `frontend/src/components/` — upload/, results/, documents/
- `frontend/src/hooks/` — useUpload (mutation), useDocumentStatus (polling 2s)
- `frontend/src/services/api.ts` — Centralized Axios client
- `frontend/src/types/document.ts` — TypeScript interfaces mirroring backend schemas

## Libraries

Backend: FastAPI, SQLAlchemy, Alembic, pydantic-settings, Celery + Redis, google-generativeai, pdf2image, opencv-python-headless, Pillow.
Frontend: Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, TanStack React Query, Axios, react-dropzone, shadcn/ui, sonner, lucide-react.

## Build & Run

Always run inside Docker containers, never on host.

- Start: `docker compose up --build`
- Migrations: `docker compose run --rm backend alembic upgrade head`
- New migration: `docker compose run --rm backend alembic revision --autogenerate -m "msg"`
- Logs: `docker compose logs -f backend`
- Stop: `docker compose down`

## API Endpoints

- `GET /health` → `{"status": "ok"}`
- `POST /api/upload` → Upload PDF, returns DocumentRead (sync or async)
- `POST /api/process/{id}` → Reprocess document via Celery
- `GET /api/results/{id}` → Get document with OCR results (404 if not found)
- `GET /api/documents` → List all documents

## Coding Standards

Use Python 3.11+ type hints everywhere (`X | None` not `Optional[X]`). Use f-strings. Enums inherit `str, enum.Enum`. snake_case files/functions, PascalCase classes, UPPER_SNAKE_CASE constants. Private methods prefixed with `_`.

Use TypeScript strict mode. No `any` types — use `unknown` if needed. PascalCase component files, camelCase hooks/services. Import alias `@/*`. Union types as string literals.

## Design Principles

- Repository pattern: all DB operations via `DocumentRepository`, no raw SQL
- Service layer: `PDFService` (preprocessing only), `GeminiOCRService` (OCR only) via `OCRService` ABC
- Routes only validate input, delegate to services/repositories, return Pydantic schemas
- Config via `pydantic BaseSettings` with `@lru_cache`, access through `app.config.settings`
- Frontend hooks encapsulate all data-fetching (TanStack Query). Components never call API directly
- Single responsibility components: UploadZone, TableRenderer, FieldsRenderer each do one thing
- All HTTP calls through `src/services/api.ts` shared Axios instance

## Security

- Never commit `.env` or `.env.local` files
- Only accept `application/pdf` uploads
- UUID primary keys, no sequential IDs
- No raw SQL — SQLAlchemy ORM only
- CORS `allow_origins=["*"]` is dev-only — restrict in production
- Celery tasks must catch exceptions and set document status to `failed`

## OCR Response Format

All results follow: `{texto: string, tablas: [{headers: string[], rows: string[][]}], campos: {key: value}}`
