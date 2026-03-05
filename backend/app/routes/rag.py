from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.logger import get_logger
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.rag_service import RagService

logger = get_logger("ocr.rag")

router = APIRouter(prefix="/api", tags=["rag"])


class IndexResponse(BaseModel):
    document_id: UUID
    chunks_indexed: int
    already_indexed: bool


class ChatRequest(BaseModel):
    question: str


class ChatSource(BaseModel):
    chunk_index: int
    content: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]


@router.post("/rag/{document_id}", response_model=IndexResponse)
def index_document(document_id: UUID, db: Session = Depends(get_db)) -> IndexResponse:
    doc_repo = DocumentRepository(db)
    document = doc_repo.get_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status != "completed":
        raise HTTPException(
            status_code=400, detail="Document has not been processed yet"
        )
    if not document.raw_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    chunk_repo = ChunkRepository(db)
    already_indexed = chunk_repo.count_by_document(document_id) > 0

    rag = RagService()
    count = rag.index_document(document_id, document.raw_text, chunk_repo)
    logger.info("Indexed document_id=%s chunks=%d", document_id, count)
    return IndexResponse(
        document_id=document_id, chunks_indexed=count, already_indexed=already_indexed
    )


@router.post("/chat/{document_id}", response_model=ChatResponse)
def chat(
    document_id: UUID,
    body: ChatRequest = Body(...),
    db: Session = Depends(get_db),
) -> ChatResponse:
    doc_repo = DocumentRepository(db)
    document = doc_repo.get_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_repo = ChunkRepository(db)
    if chunk_repo.count_by_document(document_id) == 0:
        raise HTTPException(
            status_code=400,
            detail="Document not indexed yet. Call POST /api/rag/{id} first.",
        )

    rag = RagService()
    result = rag.answer(document_id, body.question, chunk_repo)
    return ChatResponse(
        answer=result["answer"],
        sources=[ChatSource(**s) for s in result["sources"]],
    )
