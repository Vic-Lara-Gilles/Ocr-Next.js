from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentRead

router = APIRouter(prefix="/api", tags=["results"])


@router.get("/results/{document_id}", response_model=DocumentRead)
def get_document_result(document_id: UUID, db: Session = Depends(get_db)) -> DocumentRead:
	repository = DocumentRepository(db)
	document = repository.get_by_id(document_id)
	if document is None:
		raise HTTPException(status_code=404, detail="Document not found")
	return DocumentRead.model_validate(document)


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentRead]:
	repository = DocumentRepository(db)
	documents = repository.list_all()
	return [DocumentRead.model_validate(document) for document in documents]
