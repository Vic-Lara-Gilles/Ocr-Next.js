import enum
import uuid

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentStatus(str, enum.Enum):
	PENDING = "pending"
	PROCESSING = "processing"
	COMPLETED = "completed"
	FAILED = "failed"


class Document(Base):
	__tablename__ = "documents"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	filename: Mapped[str] = mapped_column(String(255), nullable=False)
	status: Mapped[DocumentStatus] = mapped_column(
		Enum(DocumentStatus, name="document_status"), nullable=False, default=DocumentStatus.PENDING
	)
	pages_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
	structured_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
	created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at: Mapped[DateTime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
	)
