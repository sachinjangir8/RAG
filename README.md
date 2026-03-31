# 🧠 DocMind — RAG Chatbot (Industry-Level)

Chat with **any document** using Gemini + Cohere + Qdrant (local). 100% Free.

---

## 🏗️ Architecture

```
User uploads file
       │
       ▼
┌─────────────────┐
│ DocumentProcessor│  Extract text from PDF/DOCX/CSV/XLSX/PPTX/TXT/JSON...
└────────┬────────┘
         │ raw text
         ▼
┌─────────────────┐
│  Text Splitter  │  Chunk (600 tokens, 80 overlap)
└────────┬────────┘
         │ chunks[]
         ▼
┌─────────────────┐
│  Cohere Embedder│  embed-english-v3.0 → 1024-dim vectors
└────────┬────────┘
         │ vectors[]
         ▼
┌─────────────────┐
│  Qdrant (local) │  Store vectors + payload
└─────────────────┘

User asks question
       │
       ▼
┌─────────────────┐
│  Cohere Embedder│  embed query (search_query type)
└────────┬────────┘
         │ query vector
         ▼
┌─────────────────┐
│  Qdrant Search  │  Top-K cosine similarity search (session-scoped)
└────────┬────────┘
         │ relevant chunks
         ▼
┌─────────────────┐
│ Gemini 2.0 Flash │  RAG prompt → answer with citations (with fallback)
└────────┬────────┘
         │ answer + sources
         ▼
      Frontend UI
```

---

## 🚀 Quick Setup

### Step 1 — Start Qdrant (Docker required)

```bash
docker-compose up -d
```

> Verify Qdrant is running: http://localhost:6333/dashboard

### Step 2 — Install Python dependencies

Create and activate a virtual environment, then run:
```bash
pip install -r requirements.txt
```

### Step 3 — Run the API

Run the application as a module using `uvicorn`:
```bash
python -m uvicorn src.main:app --reload --port 8000
```
*(Note: If you are using a virtual environment in Powershell, you may need to use `.\venv\Scripts\python -m uvicorn src.main:app --reload --port 8000`)*

### Step 4 — Open the UI

Open your browser: **http://localhost:8000**

---

## 📁 Project Structure

```
rag-project/
├── src/
│   ├── main.py              # FastAPI app — all endpoints
│   ├── rag_engine.py        # Core pipeline orchestrator
│   ├── document_processor.py# File extraction (all types)
│   ├── embedder.py          # Cohere embeddings
│   ├── vector_store.py      # Qdrant CRUD operations
│   ├── llm.py               # Gemini chat + RAG prompting + Fallback
│   └── config.py            # Centralized settings
├── index.html           # Frontend UI (dark, professional)
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Qdrant local setup
└── .env                 # API keys & config
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve UI |
| GET | `/health` | Health check |
| GET | `/stats` | Qdrant collection stats |
| POST | `/upload` | Upload & ingest file |
| POST | `/chat` | Chat (full response) |
| POST | `/stream-chat` | Chat (streaming SSE) |
| GET | `/session/{id}/files` | List session files |
| DELETE | `/session/{id}` | Clear session data |

---

## 📄 Supported File Types

| Type | Extension |
|------|-----------|
| PDF | `.pdf` |
| Word | `.docx`, `.doc` |
| Text | `.txt`, `.md`, `.rst`, `.log` |
| CSV | `.csv` |
| Excel | `.xlsx`, `.xls` |
| PowerPoint | `.pptx` |
| JSON | `.json` |
| HTML | `.html`, `.htm` |

---

## ⚙️ Configuration (`.env`)

```env
GEMINI_API_KEY=your_key
COHERE_API_KEY=your_key
QDRANT_HOST=localhost
QDRANT_PORT=6333
MAX_FILE_SIZE_MB=500
CHUNK_SIZE=600
CHUNK_OVERLAP=80
TOP_K_RESULTS=5
```

---

## 🆓 Free Tier Limits

| Service | Free Limit |
|---------|-----------|
| Gemini 2.0 Flash | 1,500 req/day, 1M tokens/min |
| Cohere embed-v3 | 1,000 req/month |
| Qdrant (local) | Unlimited (runs on your machine) |

---

## 🛠️ Troubleshooting

**Qdrant not connecting?**
```bash
docker ps          # Check if qdrant container is running
docker-compose up  # Start it
```

**Import errors?**
```bash
pip install -r requirements.txt --upgrade
```

**Large file slow?**
- Chunking + embedding large files takes time — this is normal
- Files up to 500MB are supported
- Cohere batches 96 chunks at a time
