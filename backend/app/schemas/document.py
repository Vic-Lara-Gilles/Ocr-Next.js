from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
	filename: str
	pages_count: int


class DocumentRead(BaseModel):
	id: UUID
	filename: str
	status: str
	pages_count: int
	raw_text: str | None
	structured_json: dict | None
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(from_attributes=True)


class DocumentResult(BaseModel):
	texto: str
	tablas: list[dict]
	campos: dict[str, str]
