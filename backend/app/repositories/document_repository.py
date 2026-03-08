from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: UUID) -> Document | None:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def list_all(self) -> list[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).all()

    def list_by_user(self, user_id: UUID) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    def create(
        self,
        filename: str,
        pages_count: int,
        status: DocumentStatus = DocumentStatus.PENDING,
        user_id: UUID | None = None,
    ) -> Document:
        document = Document(
            filename=filename, pages_count=pages_count, status=status, user_id=user_id
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_status(self, document: Document, status: DocumentStatus) -> Document:
        document.status = status
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_result(
        self, document: Document, raw_text: str, structured_json: dict[str, Any]
    ) -> Document:
        document.raw_text = raw_text
        document.structured_json = structured_json
        document.status = DocumentStatus.COMPLETED
        self.db.commit()
        self.db.refresh(document)
        return document
