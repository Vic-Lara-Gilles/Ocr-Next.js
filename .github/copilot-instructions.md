# OCR Platform

Document OCR system that extracts text, tables, and structured data from PDFs using Google Gemini 2.0 Flash. Small PDFs (< 5 pages) processed synchronously; larger PDFs dispatched to Celery worker asynchronously.

## Architecture

5 Docker services on `ocr-network`: FastAPI backend (:8000), Next.js 16 frontend (:3000), PostgreSQL 15 (:5432), Redis 7 (:6379), Celery worker. Dependencies: db + redis → backend → frontend; db + redis → celery.

Backend follows layered architecture: Routes → Services → Repositories → Models → Database. Frontend uses: Pages → Components → Hooks → Services → Types.

## Folder Structure

- `backend/main.py` — FastAPI app, CORS, routers, `/health`
- `backend/app/` — config.py, database.py, dependencies.py, models/, schemas/, repositories/, services/, routes/, tasks/
- `backend/app/dependencies.py` — `get_current_user` auth dependency (HTTPBearer + JWT)
- `backend/app/models/` — Document, DocumentChunk, User
- `backend/app/services/` — GeminiOCRService, PDFService, RAGService, AuthService
- `backend/app/repositories/` — DocumentRepository, ChunkRepository, UserRepository
- `backend/app/routes/` — upload, results, process, rag, auth
- `backend/app/schemas/` — document.py, user.py
- `backend/alembic/` — Database migrations (autogenerate)
- `frontend/src/app/` — App Router pages (landing, dashboard, results/[id], chat/[id], login, register)
- `frontend/src/components/` — Navbar, ProtectedRoute, upload/, results/, documents/, ui/
- `frontend/src/hooks/` — useUpload (mutation), useDocumentStatus (polling 2s), useAuth (context+hook), useRag
- `frontend/src/services/api.ts` — Centralized Axios client with Bearer token interceptor
- `frontend/src/types/` — document.ts, auth.ts

## Libraries

Backend: FastAPI, SQLAlchemy, Alembic, pydantic-settings, Celery + Redis, google-generativeai, pdf2image, opencv-python-headless, Pillow, bcrypt, PyJWT, pydantic[email].
Frontend: Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, TanStack React Query, Axios, react-dropzone, shadcn/ui, sonner, lucide-react, next-themes.

## Build & Run

Always run inside Docker containers, never on host.

- Start: `docker compose up --build`
- Migrations: `docker compose run --rm backend alembic upgrade head`
- New migration: `docker compose run --rm backend alembic revision --autogenerate -m "msg"`
- Logs: `docker compose logs -f backend`
- Stop: `docker compose down`

## API Endpoints

Public:
- `GET /health` → `{"status": "ok"}`
- `POST /api/auth/register` → Create user, returns TokenResponse (201)
- `POST /api/auth/login` → Authenticate user, returns TokenResponse (200)

Protected (require `Authorization: Bearer <token>`):
- `GET /api/auth/me` → Get current user profile
- `POST /api/upload` → Upload PDF, returns DocumentRead (sync or async)
- `POST /api/process/{id}` → Reprocess document via Celery
- `GET /api/results/{id}` → Get document with OCR results (404 if not found)
- `GET /api/documents` → List current user's documents
- `POST /api/rag/query` → Query document via RAG
- `GET /api/rag/{id}/chunks` → Get document chunks

## Coding Standards

Use Python 3.11+ type hints everywhere (`X | None` not `Optional[X]`). Use f-strings. Enums inherit `str, enum.Enum`. snake_case files/functions, PascalCase classes, UPPER_SNAKE_CASE constants. Private methods prefixed with `_`.

Use TypeScript strict mode. No `any` types — use `unknown` if needed. PascalCase component files, camelCase hooks/services. Import alias `@/*`. Union types as string literals.

## Design Principles

- Repository pattern: all DB operations via `DocumentRepository`, `UserRepository`, `ChunkRepository`, no raw SQL
- Service layer: `PDFService` (preprocessing only), `GeminiOCRService` (OCR only) via `OCRService` ABC, `AuthService` (bcrypt + JWT), `RAGService` (embeddings + search)
- Auth dependency: `get_current_user` via `dependencies.py` — HTTPBearer extracts JWT, decodes, returns User
- Routes only validate input, delegate to services/repositories, return Pydantic schemas
- Config via `pydantic BaseSettings` with `@lru_cache`, access through `app.config.settings`
- Documents are scoped to users via `user_id` foreign key — routes enforce ownership checks
- Frontend hooks encapsulate all data-fetching (TanStack Query). Components never call API directly
- `useAuth` hook provides AuthContext (login, register, logout, user state) via React Context
- `ProtectedRoute` component wraps authenticated pages, redirects to `/login` if unauthenticated
- Dark/light theme via `next-themes` ThemeProvider with `attribute="class"`, `defaultTheme="system"`
- Single responsibility components: UploadZone, TableRenderer, FieldsRenderer each do one thing
- All HTTP calls through `src/services/api.ts` shared Axios instance with Bearer token interceptor

## Security

- Authentication: bcrypt password hashing + JWT (HS256) tokens via PyJWT
- All API routes (except `/health`, `/api/auth/register`, `/api/auth/login`) require valid Bearer token
- JWT_SECRET must be a strong random value in production (never use default)
- Never commit `.env` or `.env.local` files
- Only accept `application/pdf` uploads
- UUID primary keys, no sequential IDs
- No raw SQL — SQLAlchemy ORM only
- CORS `allow_origins=["*"]` is dev-only — restrict in production
- Celery tasks must catch exceptions and set document status to `failed`
- Frontend stores JWT in localStorage; Axios interceptor auto-attaches Bearer header

## OCR Response Format

All results follow: `{texto: string, tablas: [{headers: string[], rows: string[][]}], campos: {key: value}}`
