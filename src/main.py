"""
RAG Chatbot API — FastAPI backend
Endpoints: /upload, /chat, /stream-chat, /session, /health, /stats
"""
import os, sys
sys.path.append(os.path.dirname(__file__))

import uuid
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger

from rag_engine import RAGEngine
from config import get_settings

settings = get_settings()

# ── Startup / shutdown ──────────────────────────────────────────────────────

rag: RAGEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag
    logger.info("Starting RAG Chatbot API...")
    rag = RAGEngine()
    logger.success("RAG Engine ready. API is live.")
    yield
    logger.info("Shutting down...")


# ── FastAPI app ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Chatbot API",
    description="Chat with your documents using Gemini + Cohere + Qdrant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ─────────────────────────────────────────────────────────


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    session_id: str
    history: List[ChatMessage] = []
    filename_filter: Optional[str] = None


class SessionDeleteRequest(BaseModel):
    session_id: str


# ── Routes ──────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the frontend UI."""
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "qdrant": f"{settings.qdrant_host}:{settings.qdrant_port}"}


@app.get("/stats")
async def stats():
    """Collection statistics."""
    return rag.get_stats()


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(default=None),
):
    """
    Upload and ingest a document.
    Returns session_id + ingestion stats.
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    # Read file bytes
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(400, "Uploaded file is empty.")

    try:
        result = await rag.ingest_file(
            file_bytes=file_bytes,
            filename=file.filename,
            session_id=session_id,
        )
        return {
            "success": True,
            "session_id": session_id,
            "file_info": result,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.exception("Unexpected error during upload")
        raise HTTPException(500, f"Internal error: {str(e)}")


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Non-streaming chat endpoint.
    Returns full answer + source citations.
    """
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty.")

    # Check session has documents
    files = rag.get_session_files(req.session_id)
    if not files:
        raise HTTPException(400, "No documents found for this session. Please upload a file first.")

    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        result = rag.query(
            question=req.question,
            session_id=req.session_id,
            chat_history=history,
            filename_filter=req.filename_filter,
        )
        return result
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(500, f"Error generating answer: {str(e)}")


@app.post("/stream-chat")
async def stream_chat(req: ChatRequest):
    """
    Streaming chat endpoint — returns Server-Sent Events.
    """
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty.")

    files = rag.get_session_files(req.session_id)
    if not files:
        raise HTTPException(400, "No documents found for this session.")

    history = [{"role": m.role, "content": m.content} for m in req.history]

    async def event_stream():
        try:
            async for token in rag.stream_query(
                question=req.question,
                session_id=req.session_id,
                chat_history=history,
                filename_filter=req.filename_filter,
            ):
                # SSE format
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/session/{session_id}/files")
async def get_session_files(session_id: str):
    """List all files indexed in a session."""
    files = rag.get_session_files(session_id)
    return {"session_id": session_id, "files": files}


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete all data for a session."""
    rag.delete_session(session_id)
    return {"success": True, "message": f"Session {session_id} deleted."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
