---
applyTo: "backend/**"
---

# Backend Instructions

## Layered Architecture

Routes → Services → Repositories → Models. Never skip layers.

- Routes: validate input, delegate to services/repositories, return Pydantic schemas. No business logic.
- Services: `PDFService` handles PDF-to-image + preprocessing (deskew, denoise). `GeminiOCRService` handles OCR via `OCRService(abc.ABC)`. No OCR in PDFService. No preprocessing in GeminiOCRService.
- Repositories: `DocumentRepository` accepts `db: Session` via constructor. All DB via SQLAlchemy ORM. No raw SQL.
- Models: SQLAlchemy `mapped_column` style. `DocumentStatus(str, enum.Enum)` with values: pending, processing, completed, failed.

## Configuration

All env vars loaded via `pydantic BaseSettings` with `@lru_cache(maxsize=1)` in `app/config.py`. Access through `app.config.settings`. Fields: GEMINI_API_KEY, DATABASE_URL, REDIS_URL, MAX_SYNC_PAGES (default 5), TEMP_DIR (default /tmp/ocr_uploads).

## Repository Pattern

```python
@router.get("/api/example")
def example(db: Session = Depends(get_db)):
    repository = DocumentRepository(db)
    # use repository methods: get_by_id, create, update_status, update_result, list_all
```

## Celery Tasks

Tasks use `SessionLocal()` directly (not `Depends`). Always close DB session in `finally`. Set status to `failed` on exception.

```python
@celery_app.task(name="app.tasks.module.task_name")
def task_name(document_id: str) -> None:
    db = SessionLocal()
    try:
        # do work
    except Exception:
        # update status to failed
        raise
    finally:
        db.close()
```

## Pydantic Schemas

All API responses use Pydantic models with `model_config = ConfigDict(from_attributes=True)`. Use `UUID` type for id, `datetime` for timestamps, `X | None` for nullable fields.

## Adding a New OCR Provider

1. Create class extending `OCRService` in `app/services/`
2. Implement `process_image(self, image: Image.Image) -> dict[str, Any]`
3. Return format: `{texto: str, tablas: [{headers, rows}], campos: {key: value}}`
4. Swap in routes/tasks without modifying existing providers

## Adding a New Endpoint

1. Model in `app/models/` → 2. Alembic migration → 3. Pydantic schema in `app/schemas/` → 4. Repository method → 5. Service if needed → 6. Route in `app/routes/` → 7. Register router in `main.py`

## Naming Conventions

- Files: `snake_case` (`document_repository.py`)
- Classes: `PascalCase` (`DocumentRepository`)
- Functions: `snake_case` (`update_status()`)
- Constants: `UPPER_SNAKE_CASE` (`MAX_SYNC_PAGES`)
- Private: `_leading_underscore` (`_merge_results()`)
- Type hints: always, use `X | None` not `Optional[X]`
- Enums: `class Name(str, enum.Enum)`
- Strings: f-strings

## Migrations

Always run inside container:
- Apply: `docker compose run --rm backend alembic upgrade head`
- Create: `docker compose run --rm backend alembic revision --autogenerate -m "description"`
- `alembic/env.py` must import `Base` and all models for autogenerate to work

## Troubleshooting

- DB connection fails → check `db` service health: `docker compose ps`
- Alembic fails → ensure `alembic/env.py` imports `Base` and all models
- PDF processing fails → `poppler-utils` must be in Dockerfile
- OpenCV error → `libgl1-mesa-glx` or `libgl1` must be installed
- Celery not picking up → check redis health, verify `REDIS_URL`
- Gemini empty response → verify `GEMINI_API_KEY` has quota
