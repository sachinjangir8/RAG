"""
Embedder — uses Cohere embed-english-v3.0 for semantic embeddings.
Handles batching and retry logic for large documents.
"""
import time
from typing import List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

import cohere

from config import get_settings

settings = get_settings()

# Cohere embed batch limit
COHERE_BATCH_SIZE = 96


class Embedder:
    def __init__(self):
        self.client = cohere.Client(settings.cohere_api_key)
        self.model = "embed-english-v3.0"
        logger.info("Embedder initialized with Cohere embed-english-v3.0")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _embed_batch(self, texts: List[str], input_type: str) -> List[List[float]]:
        """Embed a single batch with retry logic."""
        response = self.client.embed(
            texts=texts,
            model=self.model,
            input_type=input_type,
        )
        return response.embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed document chunks (stored in vector DB).
        Uses 'search_document' input type for asymmetric retrieval.
        """
        all_embeddings = []
        total = len(texts)
        logger.info(f"Embedding {total} document chunks...")

        for i in range(0, total, COHERE_BATCH_SIZE):
            batch = texts[i : i + COHERE_BATCH_SIZE]
            batch_num = i // COHERE_BATCH_SIZE + 1
            total_batches = (total + COHERE_BATCH_SIZE - 1) // COHERE_BATCH_SIZE
            logger.debug(f"Embedding batch {batch_num}/{total_batches}")

            embeddings = self._embed_batch(batch, input_type="search_document")
            all_embeddings.extend(embeddings)

            # Small delay to stay within rate limits
            if i + COHERE_BATCH_SIZE < total:
                time.sleep(0.1)

        logger.success(f"Embedded {len(all_embeddings)} document chunks")
        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a user query.
        Uses 'search_query' input type for asymmetric retrieval.
        """
        embeddings = self._embed_batch([query], input_type="search_query")
        return embeddings[0]
