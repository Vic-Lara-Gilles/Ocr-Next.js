from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentRead
from app.tasks.ocr_task import process_document_task

router = APIRouter(prefix="/api", tags=["process"])


@router.post("/process/{document_id}", response_model=DocumentRead)
def process_document(document_id: UUID, db: Session = Depends(get_db)) -> DocumentRead:
	repository = DocumentRepository(db)
	document = repository.get_by_id(document_id)
	if document is None:
		raise HTTPException(status_code=404, detail="Document not found")

	if document.status in {DocumentStatus.COMPLETED, DocumentStatus.PROCESSING}:
		return DocumentRead.model_validate(document)

	document = repository.update_status(document, DocumentStatus.PROCESSING)
	process_document_task.delay(str(document.id))
	return DocumentRead.model_validate(document)
