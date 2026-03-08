from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.logger import get_logger
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.upload_service import UploadService

logger = get_logger("ocr.upload")

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    service = UploadService(db)
    document = service.process_upload(file, user_id=current_user.id)
    return DocumentRead.model_validate(document)
