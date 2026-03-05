from __future__ import annotations

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pdf2image import pdfinfo_from_path
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentRead
from app.services.gemini_service import GeminiOCRService
from app.services.pdf_service import PDFService
from app.tasks.ocr_task import process_document_task

router = APIRouter(prefix="/api", tags=["upload"])


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


@router.post("/upload", response_model=DocumentRead)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DocumentRead:
	if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
		raise HTTPException(status_code=400, detail="Only PDF files are accepted")

	os.makedirs(settings.TEMP_DIR, exist_ok=True)
	staging_name = f"{uuid.uuid4()}-{file.filename}"
	staging_path = os.path.join(settings.TEMP_DIR, staging_name)

	with open(staging_path, "wb") as buffer:
		shutil.copyfileobj(file.file, buffer)

	pdf_info = pdfinfo_from_path(staging_path)
	pages_count = int(pdf_info.get("Pages", 0))

	repository = DocumentRepository(db)
	document = repository.create(filename=file.filename, pages_count=pages_count, status=DocumentStatus.PENDING)

	final_pdf_path = os.path.join(settings.TEMP_DIR, f"{document.id}.pdf")
	os.replace(staging_path, final_pdf_path)

	if pages_count < settings.MAX_SYNC_PAGES:
		try:
			repository.update_status(document, DocumentStatus.PROCESSING)
			pdf_service = PDFService()
			ocr_service = GeminiOCRService()
			images = pdf_service.process_pdf(final_pdf_path)
			page_results = [ocr_service.process_image(image) for image in images]
			raw_text, structured_json = _merge_results(page_results)
			document = repository.update_result(document, raw_text=raw_text, structured_json=structured_json)
		except Exception as exc:
			repository.update_status(document, DocumentStatus.FAILED)
			raise HTTPException(status_code=500, detail=f"Processing error: {exc}") from exc
	else:
		document = repository.update_status(document, DocumentStatus.PROCESSING)
		process_document_task.delay(str(document.id))

	return DocumentRead.model_validate(document)
