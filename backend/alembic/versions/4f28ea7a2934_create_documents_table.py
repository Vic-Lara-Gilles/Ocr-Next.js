"""create documents table

Revision ID: 4f28ea7a2934
Revises:
Create Date: 2026-03-05 13:49:24.157514

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4f28ea7a2934"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE document_status AS ENUM ('pending', 'processing', 'completed', 'failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id UUID NOT NULL,
            filename VARCHAR(255) NOT NULL,
            status document_status NOT NULL DEFAULT 'pending',
            pages_count INTEGER NOT NULL DEFAULT 0,
            raw_text TEXT,
            structured_json JSON,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP TYPE IF EXISTS document_status")
