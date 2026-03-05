"""add document_chunks table with pgvector

Revision ID: a1b2c3d4e5f6
Revises: 4f28ea7a2934
Create Date: 2026-03-05 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4f28ea7a2934"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID NOT NULL,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(768) NOT NULL,
            PRIMARY KEY (id)
        )
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
        ON document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_chunks")
