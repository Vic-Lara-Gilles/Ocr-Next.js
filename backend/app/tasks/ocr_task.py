from __future__ import annotations

import os
from uuid import UUID

from app.config import settings
from app.database import SessionLocal
from app.logger import get_logger
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.gemini_service import GeminiOCRService
from app.services.pdf_service import PDFService
from app.tasks.celery_app import celery_app

logger = get_logger("ocr.task")


def _merge_results(results: list[dict]) -> tuple[str, dict]:
    full_text = "\n\n".join(
        r.get("texto", "") for r in results if isinstance(r, dict)
    ).strip()
    tables = []
    fields: dict[str, str] = {}

    for result in results:
        if not isinstance(result, dict):
            continue
        tables.extend(result.get("tablas", []))
        for key, value in result.get("campos", {}).items():
            fields[str(key)] = str(value)

    return full_text, {"texto": full_text, "tablas": tables, "campos": fields}


@celery_app.task(name="app.tasks.ocr_task.process_document_task")
def process_document_task(document_id: str) -> None:
    logger.info("Task started document_id=%s", document_id)
    db = SessionLocal()
    repository = DocumentRepository(db)
    try:
        document = repository.get_by_id(UUID(document_id))
        if document is None:
            logger.warning("Task skipped — document not found id=%s", document_id)
            return

        pdf_path = os.path.join(settings.TEMP_DIR, f"{document.id}.pdf")
        repository.update_status(document, DocumentStatus.PROCESSING)

        pdf_service = PDFService()
        ocr_service = GeminiOCRService()
        images = pdf_service.process_pdf(pdf_path)
        logger.info("PDF rendered id=%s pages=%d", document_id, len(images))

        page_results = [ocr_service.process_image(image) for image in images]
        raw_text, structured_json = _merge_results(page_results)
        repository.update_result(
            document, raw_text=raw_text, structured_json=structured_json
        )
        logger.info("Task complete id=%s", document_id)
    except Exception as exc:
        logger.error("Task failed id=%s: %s", document_id, exc, exc_info=True)
        document = repository.get_by_id(UUID(document_id))
        if document is not None:
            repository.update_status(document, DocumentStatus.FAILED)
        raise
    finally:
        db.close()
