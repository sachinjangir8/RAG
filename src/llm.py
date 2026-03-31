"""
LLM — Google Gemini 1.5 Flash for answer generation.
Uses the new google-genai SDK (genai.Client).
"""
from typing import List, AsyncGenerator
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from google import genai

from config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are an expert document analyst and AI assistant. Your job is to answer questions accurately and thoroughly based ONLY on the provided document context.

RULES:
1. Answer ONLY from the provided context chunks. Do NOT use outside knowledge.
2. If the answer is not in the context, say: "I couldn't find information about that in the uploaded document(s)."
3. Always be specific — quote or reference the relevant part of the document when helpful.
4. If multiple documents are provided, clearly indicate which document your answer comes from.
5. Format your answers with clear structure: use bullet points, numbered lists, or paragraphs as appropriate.
6. For technical content (code, formulas, tables), preserve the original formatting.
7. Be concise but complete. Don't pad the answer unnecessarily.
"""

# Use newer gemini model available on the API key
MODEL = "gemini-2.0-flash"


class GeminiLLM:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        logger.info(f"GeminiLLM initialized with {MODEL}")

    def _build_rag_prompt(
        self,
        query: str,
        context_chunks: List[dict],
        chat_history: List[dict],
    ) -> str:
        """Construct the full RAG prompt with context and history."""
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            context_parts.append(
                f"[SOURCE {i} | File: {chunk['filename']} | "
                f"Chunk {chunk['chunk_index']+1}/{chunk['total_chunks']} | "
                f"Relevance: {chunk['score']}]\n{chunk['text']}"
            )
        context_str = "\n\n---\n\n".join(context_parts)

        history_parts = []
        for turn in chat_history[-6:]:
            role = "User" if turn["role"] == "user" else "Assistant"
            history_parts.append(f"{role}: {turn['content']}")
        history_str = "\n".join(history_parts)

        return f"""=== DOCUMENT CONTEXT ===
{context_str}

=== CONVERSATION HISTORY ===
{history_str if history_str else "(No previous conversation)"}

=== CURRENT QUESTION ===
{query}

Please answer the question based on the document context above."""

    def generate_answer(
        self,
        query: str,
        context_chunks: List[dict],
        chat_history: List[dict],
    ) -> str:
        """Generate a complete answer (non-streaming)."""
        prompt = self._build_rag_prompt(query, context_chunks, chat_history)
        logger.debug(f"Generating answer for query: {query[:60]}...")

        try:
            return self._generate_with_retry(prompt)
        except Exception as e:
            logger.error(f"Gemini LLM failed: {e}. Using fallback.")
            return "[WARNING: Gemini API Quota Exhausted or Error. Fallback Answer] Based on the context provided, this is a simulated response because the LLM rate limit was reached."

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate_with_retry(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=MODEL,
            contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
        )
        logger.success("Answer generated")
        return response.text

    async def stream_answer(
        self,
        query: str,
        context_chunks: List[dict],
        chat_history: List[dict],
    ) -> AsyncGenerator[str, None]:
        """Stream answer token by token for real-time UI updates."""
        prompt = self._build_rag_prompt(query, context_chunks, chat_history)
        logger.debug(f"Streaming answer for: {query[:60]}...")

        # generate_content_stream returns a synchronous iterator
        try:
            response = self.client.models.generate_content_stream(
                model=MODEL,
                contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini LLM stream failed: {e}. Using fallback.")
            yield "[WARNING: Gemini API Quota Exhausted or Error. Fallback Answer] Based on the context provided, this is a simulated response because the LLM rate limit was reached."
