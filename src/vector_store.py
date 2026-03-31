"""
Vector Store — manages Qdrant local instance.
Handles collection creation, upsert, search, and deletion.
"""
import uuid
from typing import List, Optional
from loguru import logger

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)

from config import get_settings

settings = get_settings()

# Cohere embed-english-v3.0 produces 1024-dim vectors
VECTOR_DIM = 1024


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=30,
        )
        self.collection = settings.qdrant_collection
        self._ensure_collection()
        logger.info(f"VectorStore ready → {settings.qdrant_host}:{settings.qdrant_port}")

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )
            # Create payload index for fast filtering
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name="session_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name="filename",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info(f"Created Qdrant collection: {self.collection}")

    def upsert_chunks(
        self,
        chunks: List[dict],
        embeddings: List[List[float]],
        session_id: str,
    ) -> int:
        """Insert chunks with their embeddings into Qdrant."""
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings count mismatch")

        points = []
        for chunk, vector in zip(chunks, embeddings):
            point_id = str(uuid.uuid4())
            payload = {
                "session_id": session_id,
                "text": chunk["text"],
                "chunk_index": chunk["chunk_index"],
                "total_chunks": chunk["total_chunks"],
                "filename": chunk["filename"],
                "file_type": chunk["file_type"],
                "file_size_kb": chunk["file_size_kb"],
            }
            # Add optional fields if present
            for opt in ("pages", "slides", "word_count", "char_count"):
                if opt in chunk:
                    payload[opt] = chunk[opt]

            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        # Batch upsert (Qdrant handles large batches well)
        BATCH = 100
        for i in range(0, len(points), BATCH):
            self.client.upsert(
                collection_name=self.collection,
                points=points[i : i + BATCH],
            )
        logger.success(f"Upserted {len(points)} vectors for session {session_id}")
        return len(points)

    def search(
        self,
        query_vector: List[float],
        session_id: str,
        top_k: int = 5,
        filename_filter: Optional[str] = None,
    ) -> List[dict]:
        """Semantic search within a session's documents."""
        must_conditions = [
            FieldCondition(key="session_id", match=MatchValue(value=session_id))
        ]
        if filename_filter:
            must_conditions.append(
                FieldCondition(key="filename", match=MatchValue(value=filename_filter))
            )

        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            query_filter=Filter(must=must_conditions),
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "text": r.payload["text"],
                "score": round(r.score, 4),
                "filename": r.payload.get("filename", "unknown"),
                "chunk_index": r.payload.get("chunk_index", 0),
                "total_chunks": r.payload.get("total_chunks", 0),
                "file_type": r.payload.get("file_type", ""),
            }
            for r in results
        ]

    def delete_session(self, session_id: str) -> int:
        """Remove all vectors for a given session."""
        result = self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
            ),
        )
        logger.info(f"Deleted vectors for session {session_id}")
        return result.status

    def get_session_files(self, session_id: str) -> List[str]:
        """List all filenames indexed in a session."""
        results, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
            ),
            limit=1000,
            with_payload=["filename"],
        )
        seen = set()
        files = []
        for r in results:
            fn = r.payload.get("filename")
            if fn and fn not in seen:
                seen.add(fn)
                files.append(fn)
        return files

    def collection_stats(self) -> dict:
        """Return collection info."""
        info = self.client.get_collection(self.collection)
        return {
            "total_vectors": info.points_count,
            "status": str(info.status),
        }
