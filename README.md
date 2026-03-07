# OCR Platform

Sistema de extracción de texto, tablas y datos estructurados desde documentos PDF utilizando **Google Gemini 2.5 Flash** como motor OCR. Incluye un pipeline RAG (Retrieval-Augmented Generation) que permite hacer preguntas en lenguaje natural sobre el contenido de los documentos procesados.

## Características

- **OCR con IA** — Extrae texto, tablas y campos clave-valor de PDFs usando Gemini 2.5 Flash
- **Preprocesamiento de imágenes** — Corrección automática de inclinación (deskew) y eliminación de ruido (denoise) con OpenCV
- **Procesamiento paralelo** — Múltiples páginas se procesan concurrentemente vía ThreadPoolExecutor
- **Procesamiento asíncrono** — PDFs se procesan en segundo plano con Celery + Redis
- **RAG con búsqueda híbrida** — Chunking semántico, embeddings vectoriales (pgvector) y full-text search con re-ranking RRF
- **Chat sobre documentos** — Interfaz de chat para hacer preguntas sobre el contenido de cualquier documento procesado
- **Descarga de resultados** — Exporta texto plano o JSON estructurado desde la interfaz

## Tech Stack

### Backend
| Tecnología | Propósito |
|---|---|
| FastAPI | Framework API REST |
| SQLAlchemy | ORM y modelos de datos |
| Alembic | Migraciones de base de datos |
| PostgreSQL 15 + pgvector | Base de datos relacional + búsqueda vectorial |
| Redis 7 | Message broker para Celery |
| Celery | Cola de tareas asíncronas |
| Google Gemini 2.5 Flash | Motor OCR y modelo de chat |
| Gemini Embedding 001 | Embeddings para búsqueda semántica |
| OpenCV | Preprocesamiento de imágenes |
| pdf2image + Poppler | Conversión PDF → imágenes |
| Pydantic Settings | Configuración tipada vía variables de entorno |

### Frontend
| Tecnología | Propósito |
|---|---|
| Next.js 16 | Framework React con App Router |
| React 19 | Librería de UI |
| TypeScript 5 | Tipado estático |
| Tailwind CSS 4 | Estilos utilitarios |
| TanStack React Query | Estado del servidor y caching |
| Axios | Cliente HTTP |
| shadcn/ui | Componentes de UI |
| react-dropzone | Subida de archivos drag & drop |
| sonner | Notificaciones toast |
| lucide-react | Iconografía |

## Arquitectura

### Servicios Docker

```
┌─────────────────────────────────────────────────────────┐
│                      ocr-network                        │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │ Frontend │───▶│ Backend  │───▶│ PostgreSQL 15    │   │
│  │ :3000    │    │ :8000    │    │ + pgvector :5432 │   │
│  └──────────┘    └────┬─────┘    └──────────────────┘   │
│                       │                                  │
│                       ▼                                  │
│                  ┌──────────┐    ┌──────────┐           │
│                  │  Redis   │◀───│  Celery  │           │
│                  │  :6379   │    │  Worker  │           │
│                  └──────────┘    └──────────┘           │
└─────────────────────────────────────────────────────────┘
```

### Backend (Layered Architecture)

```
Routes → Services → Repositories → Models → Database
```

- **Routes** — Controladores delgados: validan input, delegan a services/repositories, retornan esquemas Pydantic
- **Services** — Lógica de negocio: `UploadService`, `PDFService`, `GeminiOCRService`, `RagService`
- **Repositories** — Acceso a datos: `DocumentRepository`, `ChunkRepository` (SQLAlchemy ORM)
- **Models** — Entidades: `Document`, `DocumentChunk`

### Frontend (Component Architecture)

```
Pages → Components → Hooks → Services → Types
```

- **Pages** — App Router: landing, dashboard, results/[id], chat/[id]
- **Components** — Organizados por feature: upload/, results/, documents/
- **Hooks** — Encapsulan toda la comunicación con el servidor (TanStack Query)
- **Services** — Cliente Axios centralizado
- **Types** — Interfaces TypeScript que reflejan los esquemas del backend

### Principios SOLID aplicados

| Principio | Implementación |
|---|---|
| **SRP** | Cada servicio tiene una única responsabilidad: `PDFService` (preprocesamiento), `GeminiOCRService` (OCR), `UploadService` (flujo de subida), `RagService` (búsqueda y chat) |
| **OCP** | `OCRService(ABC)` permite agregar nuevos providers sin modificar los existentes. `ResultViewer` acepta prop `renderers` para intercambiar renderizadores |
| **LSP** | `GeminiOCRService` extiende `OCRService` cumpliendo el contrato `process_image()` |
| **ISP** | Interfaces pequeñas y enfocadas — un hook por operación de datos |
| **DIP** | Configuración centralizada vía `pydantic BaseSettings`, repositorios inyectados vía constructor |

## API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/upload` | Subir PDF (multipart/form-data) |
| `POST` | `/api/process/{id}` | Reprocesar documento vía Celery |
| `GET` | `/api/results/{id}` | Obtener documento con resultados OCR |
| `GET` | `/api/documents` | Listar todos los documentos |
| `POST` | `/api/rag/{id}` | Indexar documento para búsqueda RAG |
| `POST` | `/api/chat/{id}` | Hacer pregunta sobre documento indexado |

### Ejemplo: Subir un PDF

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@documento.pdf"
```

Respuesta:
```json
{
  "id": "a1b2c3d4-...",
  "filename": "documento.pdf",
  "status": "processing",
  "pages_count": 3,
  "raw_text": null,
  "structured_json": null,
  "created_at": "2026-03-07T12:00:00Z",
  "updated_at": "2026-03-07T12:00:00Z"
}
```

### Ejemplo: Chat con documento

```bash
# 1. Indexar documento (una sola vez)
curl -X POST http://localhost:8000/api/rag/a1b2c3d4-...

# 2. Hacer preguntas
curl -X POST http://localhost:8000/api/chat/a1b2c3d4-... \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el monto total?"}'
```

Respuesta:
```json
{
  "answer": "El monto total es $15,000.00 según la factura.",
  "sources": [
    {"chunk_index": 2, "content": "[documento.pdf — fragmento 3/10]\nMonto total: $15,000.00..."}
  ]
}
```

## Formato de respuesta OCR

Todas las extracciones siguen este formato JSON:

```json
{
  "texto": "Texto completo extraído del documento...",
  "tablas": [
    {
      "headers": ["Columna 1", "Columna 2"],
      "rows": [["valor 1", "valor 2"]]
    }
  ],
  "campos": {
    "fecha": "07/03/2026",
    "monto_total": "$15,000.00",
    "numero_factura": "FAC-001"
  }
}
```

## Base de datos

### Tabla `documents`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID (PK) | Identificador único |
| `filename` | VARCHAR(255) | Nombre del archivo original |
| `status` | ENUM | `pending`, `processing`, `completed`, `failed` |
| `pages_count` | INTEGER | Número de páginas del PDF |
| `raw_text` | TEXT | Texto plano extraído |
| `structured_json` | JSON | Resultado estructurado (texto + tablas + campos) |
| `created_at` | TIMESTAMPTZ | Fecha de creación |
| `updated_at` | TIMESTAMPTZ | Última actualización |

### Tabla `document_chunks`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID (PK) | Identificador único |
| `document_id` | UUID (FK) | Referencia al documento |
| `chunk_index` | INTEGER | Índice del fragmento |
| `content` | TEXT | Texto del fragmento con metadata |
| `embedding` | VECTOR(768) | Embedding vectorial (Gemini Embedding 001) |

## Despliegue con Docker

### Prerrequisitos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose v2+
- API Key de [Google AI Studio](https://aistudio.google.com/apikey) (Gemini)

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd Ocr-Next.js
```

### 2. Configurar variables de entorno

```bash
# Backend
cp backend/.env.example backend/.env
# Editar backend/.env y configurar la API key de Gemini:
#   GEMINI_API_KEY=tu-api-key-real

# Frontend
cp frontend/.env.example frontend/.env.local
# Editar frontend/.env.local si es necesario:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Importante**: Nunca commitear los archivos `.env` o `.env.local`. Ya están en `.gitignore`.

### 3. Levantar los servicios

```bash
docker compose up --build -d
```

Esto crea 5 contenedores en la red `ocr-network`:

| Servicio | Puerto | Descripción |
|---|---|---|
| `frontend` | 3000 | Interfaz web Next.js |
| `backend` | 8000 | API REST FastAPI |
| `db` | 5432 | PostgreSQL 15 + pgvector |
| `redis` | 6379 | Redis 7 (broker Celery) |
| `celery` | — | Worker para procesamiento asíncrono |

### 4. Ejecutar migraciones de base de datos

```bash
docker compose run --rm backend alembic upgrade head
```

### 5. Verificar que todo funciona

```bash
# Health check del backend
curl http://localhost:8000/health
# → {"status": "ok"}

# Estado de los contenedores
docker compose ps
```

### 6. Abrir la aplicación

- **Frontend**: http://localhost:3000
- **API docs (Swagger)**: http://localhost:8000/docs
- **API docs (ReDoc)**: http://localhost:8000/redoc

### Despliegue desde cero (fresh)

Si necesitas reiniciar todo desde cero (elimina volúmenes y datos):

```bash
make fresh
```

Esto ejecuta:
1. `docker compose down -v` — Elimina contenedores y volúmenes
2. `docker system prune -f` — Limpia imágenes sin uso
3. Levanta DB y Redis, espera health checks
4. Ejecuta migraciones con Alembic
5. Construye y levanta todos los servicios

### Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f backend celery

# Reiniciar solo el backend
docker compose restart backend celery

# Reconstruir sin cache
docker compose build --no-cache

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (⚠️ borra datos)
docker compose down -v
```

### Variables de entorno

#### Backend (`backend/.env`)

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `GEMINI_API_KEY` | Sí | — | API key de Google AI Studio |
| `DATABASE_URL` | Sí | — | URL de conexión PostgreSQL |
| `REDIS_URL` | Sí | — | URL de conexión Redis |
| `MAX_SYNC_PAGES` | No | `5` | Páginas máximas para procesamiento síncrono |
| `TEMP_DIR` | No | `/tmp/ocr_uploads` | Directorio temporal para PDFs |

#### Frontend (`frontend/.env.local`)

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Sí | — | URL base del backend API |

#### Docker Compose (opcionales)

| Variable | Default | Descripción |
|---|---|---|
| `POSTGRES_USER` | `ocr` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `ocr` | Contraseña de PostgreSQL |
| `POSTGRES_DB` | `ocr` | Nombre de la base de datos |

> En producción, define `POSTGRES_PASSWORD` como variable de entorno con un valor seguro.

### Consideraciones de producción

- **CORS**: Cambiar `allow_origins=["*"]` en `main.py` por los dominios específicos del frontend
- **PostgreSQL**: Usar una contraseña segura vía `POSTGRES_PASSWORD` en el entorno
- **HTTPS**: Configurar un reverse proxy (Nginx, Traefik) con certificados TLS
- **Autenticación**: Agregar JWT o API keys si se manejan documentos sensibles
- **Volúmenes**: Los datos de PostgreSQL persisten en el volumen `postgres_data`
- **Monitoreo**: Los logs estructurados del backend se escriben a stdout — integrar con un sistema de logging centralizado

## Estructura del proyecto

```
├── docker-compose.yml          # Orquestación de 5 servicios
├── Makefile                    # Comando fresh para reset completo
├── backend/
│   ├── Dockerfile              # Python 3.11 + poppler + OpenCV
│   ├── main.py                 # FastAPI app, CORS, routers, /health
│   ├── requirements.txt        # Dependencias Python
│   ├── alembic.ini             # Configuración Alembic
│   ├── alembic/                # Migraciones de DB
│   │   └── versions/           # Scripts de migración
│   └── app/
│       ├── config.py           # Settings con pydantic-settings
│       ├── database.py         # Engine SQLAlchemy + SessionLocal
│       ├── logger.py           # Logger estructurado
│       ├── models/             # Document, DocumentChunk
│       ├── schemas/            # Pydantic: DocumentRead, DocumentResult
│       ├── repositories/       # DocumentRepository, ChunkRepository
│       ├── services/           # UploadService, PDFService, GeminiOCRService, RagService
│       ├── routes/             # upload, process, results, rag
│       └── tasks/              # Celery app + ocr_task
├── frontend/
│   ├── Dockerfile              # Node 20 Alpine + pnpm
│   ├── package.json            # Dependencias Node
│   └── src/
│       ├── app/                # App Router: landing, dashboard, results/[id], chat/[id]
│       ├── components/         # upload/, results/, documents/, ui/
│       ├── hooks/              # useUpload, useDocumentStatus, useDocuments, useRag
│       ├── services/           # api.ts (Axios client)
│       └── types/              # document.ts (interfaces TypeScript)
└── .github/
    ├── copilot-instructions.md # Instrucciones generales del proyecto
    └── instructions/           # Reglas por contexto (backend, frontend, docker, commits)
```

## Licencia

Este proyecto es de uso privado.
