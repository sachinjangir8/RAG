import asyncio
from document_processor import DocumentProcessor
from embedder import Embedder
from llm import GeminiLLM

def test_pipeline():
    print("Testing processor...")
    proc = DocumentProcessor()
    text, meta = proc.extract_text("test.txt", "test.txt")
    print(meta)
    chunks = proc.chunk_text(text, meta)
    print("Chunks:", len(chunks))

    print("Testing embedder...")
    emb = Embedder()
    try:
        vec = emb.embed_query("hello")
        print("Embed:", len(vec))
    except Exception as e:
        print("Embed error:", e)

    print("Testing LLM...")
    llm = GeminiLLM()
    try:
        ans = llm.generate_answer("hello", context_chunks=[{"text": "hello", "filename": "t", "chunk_index": 0, "total_chunks": 1, "score": 1.0}], chat_history=[])
        print("Ans:", ans[:50])
    except Exception as e:
        print("LLM error:", e)

if __name__ == "__main__":
    test_pipeline()
