from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk


class ChunkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def delete_by_document(self, document_id: UUID) -> None:
        self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        self.db.commit()

    def bulk_insert(self, chunks: list[DocumentChunk]) -> None:
        self.db.add_all(chunks)
        self.db.commit()

    def similarity_search(
        self, document_id: UUID, query_embedding: list[float], top_k: int = 5
    ) -> list[DocumentChunk]:
        results = (
            self.db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            )
            .scalars()
            .all()
        )
        return list(results)

    def count_by_document(self, document_id: UUID) -> int:
        from sqlalchemy import func

        result = self.db.execute(
            select(func.count()).where(DocumentChunk.document_id == document_id)
        ).scalar()
        return result or 0
