"""
RAG Engine — orchestrates the full pipeline:
  Upload → Extract → Chunk → Embed → Store → Query → Retrieve → Answer
"""
import os
import uuid
import tempfile
import aiofiles
from pathlib import Path
from typing import List, Optional, AsyncGenerator
from loguru import logger

from document_processor import DocumentProcessor
from embedder import Embedder
from vector_store import VectorStore
from llm import GeminiLLM
from config import get_settings

settings = get_settings()

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".rst", ".log",
    ".csv", ".xlsx", ".xls", ".pptx", ".json", ".html", ".htm",
}


class RAGEngine:
    def __init__(self):
        self.processor = DocumentProcessor()
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self.llm = GeminiLLM()
        logger.info("RAGEngine ready")

    # ── File ingestion ──────────────────────────────────────────────────────

    async def ingest_file(
        self,
        file_bytes: bytes,
        filename: str,
        session_id: str,
    ) -> dict:
        """Full pipeline: save → extract → chunk → embed → store."""
        # Validate extension
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: '{ext}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        # Validate file size
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            raise ValueError(
                f"File too large ({size_mb:.1f} MB). Max allowed: {settings.max_file_size_mb} MB"
            )

        logger.info(f"Ingesting '{filename}' ({size_mb:.2f} MB) for session {session_id}")

        # Write to temp file for processing
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            # Step 1: Extract text + metadata
            text, metadata = self.processor.extract_text(tmp_path, filename)

            if not text.strip():
                raise ValueError("No text could be extracted from this file.")

            # Step 2: Chunk
            chunks = self.processor.chunk_text(text, metadata)
            if not chunks:
                raise ValueError("Document produced no text chunks after processing.")

            # Step 3: Embed
            texts_only = [c["text"] for c in chunks]
            embeddings = self.embedder.embed_documents(texts_only)

            # Step 4: Store in Qdrant
            stored = self.vector_store.upsert_chunks(chunks, embeddings, session_id)

            result = {
                "filename": filename,
                "file_type": ext,
                "file_size_mb": round(size_mb, 3),
                "chunks_stored": stored,
                "word_count": metadata.get("word_count", 0),
                "char_count": metadata.get("char_count", 0),
            }
            if "pages" in metadata:
                result["pages"] = metadata["pages"]
            if "slides" in metadata:
                result["slides"] = metadata["slides"]

            logger.success(f"Ingestion complete: {stored} chunks stored for '{filename}'")
            return result

        finally:
            os.unlink(tmp_path)

    # ── Querying ────────────────────────────────────────────────────────────

    def query(
        self,
        question: str,
        session_id: str,
        chat_history: List[dict],
        filename_filter: Optional[str] = None,
    ) -> dict:
        """Full RAG query: embed question → retrieve → generate answer."""
        logger.info(f"Query for session {session_id}: {question[:80]}")

        # Step 1: Embed query
        query_vector = self.embedder.embed_query(question)

        # Step 2: Retrieve relevant chunks
        chunks = self.vector_store.search(
            query_vector=query_vector,
            session_id=session_id,
            top_k=settings.top_k_results,
            filename_filter=filename_filter,
        )

        if not chunks:
            return {
                "answer": "I couldn't find any relevant content in the uploaded document(s). Please make sure you've uploaded a file and try rephrasing your question.",
                "sources": [],
                "chunks_used": 0,
            }

        # Step 3: Generate answer
        answer = self.llm.generate_answer(
            query=question,
            context_chunks=chunks,
            chat_history=chat_history,
        )

        return {
            "answer": answer,
            "sources": [
                {
                    "filename": c["filename"],
                    "chunk_index": c["chunk_index"],
                    "total_chunks": c["total_chunks"],
                    "relevance_score": c["score"],
                    "excerpt": c["text"][:300] + ("..." if len(c["text"]) > 300 else ""),
                }
                for c in chunks
            ],
            "chunks_used": len(chunks),
        }

    async def stream_query(
        self,
        question: str,
        session_id: str,
        chat_history: List[dict],
        filename_filter: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming RAG query — yields answer tokens."""
        query_vector = self.embedder.embed_query(question)
        chunks = self.vector_store.search(
            query_vector=query_vector,
            session_id=session_id,
            top_k=settings.top_k_results,
            filename_filter=filename_filter,
        )

        if not chunks:
            yield "I couldn't find any relevant content in the uploaded document(s)."
            return

        async for token in self.llm.stream_answer(
            query=question,
            context_chunks=chunks,
            chat_history=chat_history,
        ):
            yield token

    # ── Session management ──────────────────────────────────────────────────

    def get_session_files(self, session_id: str) -> List[str]:
        return self.vector_store.get_session_files(session_id)

    def delete_session(self, session_id: str):
        self.vector_store.delete_session(session_id)
        logger.info(f"Session {session_id} deleted")

    def get_stats(self) -> dict:
        return self.vector_store.collection_stats()
