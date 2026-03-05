"""create documents table

Revision ID: 4f28ea7a2934
Revises:
Create Date: 2026-03-05 13:49:24.157514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4f28ea7a2934'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    document_status = sa.Enum("pending", "processing", "completed", "failed", name="document_status")
    document_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.Column("pages_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("structured_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("documents")
    document_status = sa.Enum("pending", "processing", "completed", "failed", name="document_status")
    document_status.drop(op.get_bind(), checkfirst=True)
