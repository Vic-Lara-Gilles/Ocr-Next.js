from __future__ import annotations

import os
from uuid import UUID

from app.config import settings
from app.database import SessionLocal
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.gemini_service import GeminiOCRService
from app.services.pdf_service import PDFService
from app.tasks.celery_app import celery_app


def _merge_results(results: list[dict]) -> tuple[str, dict]:
	full_text = "\n\n".join(r.get("texto", "") for r in results if isinstance(r, dict)).strip()
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
	db = SessionLocal()
	repository = DocumentRepository(db)
	try:
		document = repository.get_by_id(UUID(document_id))
		if document is None:
			return

		pdf_path = os.path.join(settings.TEMP_DIR, f"{document.id}.pdf")
		repository.update_status(document, DocumentStatus.PROCESSING)

		pdf_service = PDFService()
		ocr_service = GeminiOCRService()
		images = pdf_service.process_pdf(pdf_path)

		page_results = [ocr_service.process_image(image) for image in images]
		raw_text, structured_json = _merge_results(page_results)
		repository.update_result(document, raw_text=raw_text, structured_json=structured_json)
	except Exception:
		document = repository.get_by_id(UUID(document_id))
		if document is not None:
			repository.update_status(document, DocumentStatus.FAILED)
		raise
	finally:
		db.close()
