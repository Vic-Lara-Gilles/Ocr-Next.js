from __future__ import annotations

import os
import shutil
import uuid

from fastapi import UploadFile
from pdf2image import pdfinfo_from_path
from sqlalchemy.orm import Session

from app.config import settings
from app.logger import get_logger
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.tasks.ocr_task import process_document_task

logger = get_logger("ocr.upload")


class UploadService:
    def __init__(self, db: Session) -> None:
        self._repository = DocumentRepository(db)

    def _save_staging_file(self, file: UploadFile) -> str:
        """Save the uploaded file to a temporary staging path."""
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        staging_name = f"{uuid.uuid4()}-{file.filename}"
        staging_path = os.path.join(settings.TEMP_DIR, staging_name)
        with open(staging_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return staging_path

    def _get_page_count(self, pdf_path: str) -> int:
        pdf_info = pdfinfo_from_path(pdf_path)
        return int(pdf_info.get("Pages", 0))

    def _move_to_final_path(self, staging_path: str, document_id: uuid.UUID) -> str:
        final_path = os.path.join(settings.TEMP_DIR, f"{document_id}.pdf")
        os.replace(staging_path, final_path)
        return final_path

    def process_upload(
        self, file: UploadFile, user_id: uuid.UUID | None = None
    ) -> Document:
        """Handle the full upload flow: save, create record, dispatch task."""
        staging_path = self._save_staging_file(file)

        try:
            pages_count = self._get_page_count(staging_path)
            document = self._repository.create(
                filename=file.filename,
                pages_count=pages_count,
                status=DocumentStatus.PENDING,
                user_id=user_id,
            )
            logger.info(
                "Document created id=%s filename=%s pages=%d",
                document.id,
                file.filename,
                pages_count,
            )

            self._move_to_final_path(staging_path, document.id)
            document = self._repository.update_status(
                document, DocumentStatus.PROCESSING
            )
            process_document_task.delay(str(document.id))

            logger.info(
                "Dispatching async task id=%s pages=%d", document.id, pages_count
            )
            return document
        except Exception:
            if os.path.exists(staging_path):
                os.remove(staging_path)
            raise
