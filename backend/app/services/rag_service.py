from __future__ import annotations

import uuid
from typing import Any

from google import genai
from google.genai import types

from app.config import settings
from app.logger import get_logger
from app.models.chunk import DocumentChunk, EMBEDDING_DIM
from app.repositories.chunk_repository import ChunkRepository

logger = get_logger("ocr.rag")

# Gemini chat model for answering questions
CHAT_MODEL = "gemini-2.5-flash"
# Chunk size in characters
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


class RagService:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # ------------------------------------------------------------------ #
    # Chunking                                                             #
    # ------------------------------------------------------------------ #

    def _split_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunks.append(text[start:end].strip())
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return [c for c in chunks if c]

    # ------------------------------------------------------------------ #
    # Embeddings                                                           #
    # ------------------------------------------------------------------ #

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Batch embed using text-embedding-004 (768 dims, free tier)."""
        result = self._client.models.embed_content(
            model="text-embedding-004",
            contents=texts,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        return [e.values for e in result.embeddings]

    def _embed_query(self, text: str) -> list[float]:
        result = self._client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        return result.embeddings[0].values

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def index_document(
        self, document_id: uuid.UUID, raw_text: str, repo: ChunkRepository
    ) -> int:
        """Chunk, embed and store vectors for a document. Returns chunk count."""
        logger.info("Indexing document_id=%s", document_id)
        repo.delete_by_document(document_id)

        texts = self._split_text(raw_text)
        if not texts:
            logger.warning("No text to index for document_id=%s", document_id)
            return 0

        embeddings = self._embed(texts)
        chunks = [
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=document_id,
                chunk_index=i,
                content=text,
                embedding=emb,
            )
            for i, (text, emb) in enumerate(zip(texts, embeddings))
        ]
        repo.bulk_insert(chunks)
        logger.info("Indexed %d chunks for document_id=%s", len(chunks), document_id)
        return len(chunks)

    def answer(
        self, document_id: uuid.UUID, question: str, repo: ChunkRepository
    ) -> dict[str, Any]:
        """Find relevant chunks and generate an answer."""
        logger.info("RAG query document_id=%s question=%.80s", document_id, question)
        query_emb = self._embed_query(question)
        chunks = repo.similarity_search(document_id, query_emb, top_k=5)

        if not chunks:
            return {
                "answer": "No hay información indexada para este documento.",
                "sources": [],
            }

        context = "\n\n---\n\n".join(c.content for c in chunks)
        prompt = (
            f"Responde la siguiente pregunta usando ÚNICAMENTE el contexto provisto. "
            f"Si la respuesta no está en el contexto, di 'No encontré esa información en el documento'.\n\n"
            f"Contexto:\n{context}\n\n"
            f"Pregunta: {question}"
        )

        response = self._client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt,
        )
        answer_text = (
            response.text.strip() if response and response.text else "Sin respuesta."
        )

        return {
            "answer": answer_text,
            "sources": [
                {"chunk_index": c.chunk_index, "content": c.content[:200]}
                for c in chunks
            ],
        }
