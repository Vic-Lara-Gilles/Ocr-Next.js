from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select
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

    def vector_search(
        self,
        document_id: UUID,
        query_embedding: list[float],
        candidates: int = 20,
    ) -> list[tuple[DocumentChunk, float]]:
        """Return (chunk, cosine_distance) pairs ordered by ascending distance."""
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        rows = self.db.execute(
            select(DocumentChunk, distance.label("dist"))
            .where(DocumentChunk.document_id == document_id)
            .order_by(distance)
            .limit(candidates)
        ).all()
        return [(row.DocumentChunk, float(row.dist)) for row in rows]

    def fulltext_search(
        self,
        document_id: UUID,
        query_text: str,
        candidates: int = 20,
    ) -> list[tuple[DocumentChunk, float]]:
        """Return (chunk, ts_rank) pairs using PostgreSQL full-text search.

        Uses 'simple' config (no language-specific stemming) so it works for
        any document language. plainto_tsquery handles multi-word queries and
        special characters gracefully — never throws on user input.
        """
        tsquery = func.plainto_tsquery("simple", query_text)
        tsvector = func.to_tsvector("simple", DocumentChunk.content)
        rank = func.ts_rank(tsvector, tsquery)
        rows = self.db.execute(
            select(DocumentChunk, rank.label("rank"))
            .where(DocumentChunk.document_id == document_id)
            .where(tsvector.op("@@")(tsquery))
            .order_by(rank.desc())
            .limit(candidates)
        ).all()
        return [(row.DocumentChunk, float(row.rank)) for row in rows]

    def count_by_document(self, document_id: UUID) -> int:
        result = self.db.execute(
            select(func.count()).where(DocumentChunk.document_id == document_id)
        ).scalar()
        return result or 0
