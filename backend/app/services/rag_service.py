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
# Chunk size in characters — larger = more context per chunk
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
# How many chunks to retrieve per query
TOP_K = 8
# Separators tried in order: prefer paragraph → line → sentence → word
_SEPARATORS = ["\n\n", "\n", ". ", " "]


class RagService:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # ------------------------------------------------------------------ #
    # Chunking                                                             #
    # ------------------------------------------------------------------ #

    def _split_text(self, text: str) -> list[str]:
        """Split text on semantic boundaries (paragraph > line > sentence > word).

        For each candidate chunk that exceeds CHUNK_SIZE, we walk the separator
        list and try to cut at a natural boundary instead of mid-word/mid-sentence.
        Overlap is applied at the character level so no context is lost at edges.
        """
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            if end >= len(text):
                # last piece — take everything remaining
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # try to cut at a natural boundary within the window
            cut = end
            for sep in _SEPARATORS:
                idx = text.rfind(sep, start, end)
                if idx != -1:
                    cut = idx + len(sep)
                    break

            chunk = text[start:cut].strip()
            if chunk:
                chunks.append(chunk)
            # advance with overlap so context is not lost at chunk edges
            start = max(start + 1, cut - CHUNK_OVERLAP)

        return chunks

    # ------------------------------------------------------------------ #
    # Embeddings                                                           #
    # ------------------------------------------------------------------ #

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Batch embed using gemini-embedding-001 (768 dims via output_dimensionality)."""
        result = self._client.models.embed_content(
            model="gemini-embedding-001",
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=768,
            ),
        )
        return [e.values for e in result.embeddings]

    def _embed_query(self, text: str) -> list[float]:
        result = self._client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=768,
            ),
        )
        return result.embeddings[0].values

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def index_document(
        self, document_id: uuid.UUID, raw_text: str, repo: ChunkRepository, filename: str = ""
    ) -> int:
        """Chunk, embed and store vectors for a document. Returns chunk count."""
        logger.info("Indexing document_id=%s", document_id)
        repo.delete_by_document(document_id)

        raw_chunks = self._split_text(raw_text)
        if not raw_chunks:
            logger.warning("No text to index for document_id=%s", document_id)
            return 0

        # Mejora 3: prefix each chunk with document context so the embedding
        # carries provenance information — helps retrieval for generic phrases.
        doc_label = filename or str(document_id)
        texts_to_embed = [
            f"[{doc_label} — fragmento {i + 1}/{len(raw_chunks)}]\n{chunk}"
            for i, chunk in enumerate(raw_chunks)
        ]

        embeddings = self._embed(texts_to_embed)
        chunks = [
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=document_id,
                chunk_index=i,
                content=texts_to_embed[i],  # store the enriched version
                embedding=emb,
            )
            for i, emb in enumerate(embeddings)
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
        chunks = repo.similarity_search(document_id, query_emb, top_k=TOP_K)

        if not chunks:
            return {
                "answer": "No hay información indexada para este documento.",
                "sources": [],
            }

        # Build context block with numbered sections so the model can reference them
        context_parts = [
            f"[Fragmento {i + 1}]\n{c.content}" for i, c in enumerate(chunks)
        ]
        context = "\n\n---\n\n".join(context_parts)

        prompt = (
            f"Eres un asistente experto en análisis de documentos. "
            f"Responde la siguiente pregunta usando ÚNICAMENTE los fragmentos de contexto provistos. "
            f"Si la respuesta no está en el contexto, responde exactamente: "
            f"'No encontré esa información en el documento'.\n\n"
            f"Contexto ({len(chunks)} fragmentos recuperados):\n{context}\n\n"
            f"Pregunta: {question}\n\n"
            f"Respuesta:"
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
