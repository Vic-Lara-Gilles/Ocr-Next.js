from __future__ import annotations

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pdf2image import pdfinfo_from_path
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.logger import get_logger
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentRead
from app.tasks.ocr_task import process_document_task

logger = get_logger("ocr.upload")

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> DocumentRead:
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(
        ".pdf"
    ):
        logger.warning(
            "Rejected non-PDF upload: %s (content_type=%s)",
            file.filename,
            file.content_type,
        )
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    staging_name = f"{uuid.uuid4()}-{file.filename}"
    staging_path = os.path.join(settings.TEMP_DIR, staging_name)

    with open(staging_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pdf_info = pdfinfo_from_path(staging_path)
    pages_count = int(pdf_info.get("Pages", 0))

    repository = DocumentRepository(db)
    document = repository.create(
        filename=file.filename, pages_count=pages_count, status=DocumentStatus.PENDING
    )
    logger.info(
        "Document created id=%s filename=%s pages=%d",
        document.id,
        file.filename,
        pages_count,
    )

    final_pdf_path = os.path.join(settings.TEMP_DIR, f"{document.id}.pdf")
    os.replace(staging_path, final_pdf_path)

    logger.info("Dispatching async task id=%s pages=%d", document.id, pages_count)
    document = repository.update_status(document, DocumentStatus.PROCESSING)
    process_document_task.delay(str(document.id))

    return DocumentRead.model_validate(document)
