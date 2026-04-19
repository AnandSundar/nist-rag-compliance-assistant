# 🛡️ NIST 800-53 RAG Compliance Assistant

A production-ready AI chatbot that answers questions about NIST 800-53 security controls using Retrieval-Augmented Generation (RAG). Retrieves relevant control sections from the NIST 800-53 PDF and generates accurate, grounded answers using a free LLM without hallucinations.

![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3-orange.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)
![Deploy on Render](https://img.shields.io/badge/deploy-render-00979D.svg)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INGESTION PIPELINE (runs once)                     │
└─────────────────────────────────────────────────────────────────────────────────┘

    NIST 800-53 PDF
           │
           ▼
    ┌──────────────┐
    │ PyPDF Loader │ → Extract text from PDF
    └──────────────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ NIST-Aware Chunker           │ → Split at control boundaries (AC-1, AC-2, etc.)
    │ - Preserves control IDs      │ → Maintains context windows
    │ - 800 char chunks            │ → Overlaps for continuity
    └──────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ Gemini Text Embeddings       │ → text-embedding-004 model
    │ (Google AI Studio)           │ → 768-dimensional vectors
    └──────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ ChromaDB (persistent)        │ → Local vector database
    │ ./chroma_db/                 │ → Stored on disk
    └──────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                               QUERY PIPELINE (per question)                     │
└─────────────────────────────────────────────────────────────────────────────────┘

    User Question
           │
           ▼
    ┌──────────────────────────────┐
    │ Gemini Text Embeddings       │ → Embed user query
    └──────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ ChromaDB MMR Search          │ → Maximal Marginal Relevance
    │ (top 6 chunks)               │ → Diversity + relevance
    └──────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ CrossEncoder Reranker        │ → ms-marco-MiniLM-L-6-v2
    │ (top 3 chunks)               │ → Local HuggingFace model
    └──────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ Groq Llama 3.3 70B           │ → Generate grounded answer
    │ (llama-3.3-70b-versatile)    │ → Source citations
    └──────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ Streaming SSE Response       │ → Server-Sent Events
    │ → Real-time token streaming  │ → Chat UI updates
    └──────────────────────────────┘
```

## Features

- **NIST Control-Aware Chunking**: Intelligently splits documents at control boundaries (AC-1, AU-2, etc.) to preserve semantic meaning and control context
- **Two-Stage Retrieval**: ChromaDB MMR search for diverse results followed by CrossEncoder reranking for precision
- **Streaming Responses**: Real-time token streaming via Server-Sent Events (SSE) for responsive user experience
- **Source Citations**: Every answer includes control IDs and page numbers for verification
- **Zero Hallucination Guardrails**: System prompts explicitly instruct the LLM to say "I don't know" when the answer isn't in the context
- **Dark-Themed Responsive UI**: Modern chat interface built with vanilla HTML/CSS/JS, works on mobile and desktop
- **Docker Support**: Full containerization with pre-built ChromaDB index baked into the image
- **Free-Tier Deployment**: Runs entirely on free APIs and services ($0/month total cost)

## Prerequisites

Before you begin, ensure you have the following:

- **Python 3.12+** — Download from [python.org](https://www.python.org/downloads/)
- **Docker** (optional) — For containerized deployment, install from [docker.com](https://www.docker.com/products/docker-desktop/)
- **Google AI Studio API Key** — Free tier available at [aistudio.google.com](https://aistudio.google.com/app/apikey)
- **Groq API Key** — Free tier available at [console.groq.com](https://console.groq.com/keys)
- **NIST 800-53 Rev 5 PDF** — Download from [NIST publication page](https://csrc.nist.gov/pubs/sp/800/53/rev/5/final)

## Local Setup

Follow these steps to run the application locally:

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nist-rag.git
   cd nist-rag
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ADMIN_TOKEN=your_secure_admin_token_here
   ```

5. **Place NIST PDF in data directory**
   ```bash
   # Copy your downloaded NIST 800-53 Rev 5 PDF to:
   cp /path/to/NIST_SP-800-53_rev5.pdf data/nist.pdf
   ```

6. **Run ingestion pipeline**
   ```bash
   python main.py --ingest
   ```
   
   This will:
   - Extract text from the PDF using PyPDF
   - Split content into control-aware chunks (~800 chars each)
   - Generate embeddings using Gemini text-embedding-004
   - Store vectors in ChromaDB at `./chroma_db/`
   - Display progress bars and final chunk count
   
   Expected output:
   ```
   Loading PDF: data/nist.pdf
   Chunking document...
   Created 1,847 chunks
   Generating embeddings...
   Stored 1,847 vectors in ChromaDB
   Ingestion complete!
   ```

7. **Start the FastAPI server**
   ```bash
   uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Open the chat interface**
   
   Navigate to [http://localhost:8000](http://localhost:8000) in your browser. Start asking questions about NIST 800-53 controls!

## Docker Setup

To run the application in a Docker container:

1. **Build the Docker image**
   ```bash
   docker build -t nist-rag:latest .
   ```
   
   Note: The Dockerfile includes a build stage that runs ingestion, so the ChromaDB index is baked into the image.

2. **Run the container with environment variables**
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e GEMINI_API_KEY=your_gemini_api_key_here \
     -e GROQ_API_KEY=your_groq_api_key_here \
     -e ADMIN_TOKEN=your_secure_admin_token_here \
     --name nist-rag \
     nist-rag:latest
   ```

3. **Access the chat UI**
   
   Open [http://localhost:8000](http://localhost:8000) in your browser.

## Deploy to Render.com (Free Tier)

Deploy your application to Render.com using the free tier:

1. **Push your repository to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git push -u origin main
   ```

2. **Connect your repository to Render.com**
   - Log in to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect the Dockerfile

3. **Configure the deployment**
   - **Name**: nist-rag (or your preferred name)
   - **Region**: Oregon (free tier)
   - **Instance Type**: Free (512 MB RAM, 0.1 CPU)
   - **Branch**: main

4. **Set environment variables** (in "Advanced" section)
   | Key | Value |
   |-----|-------|
   | GEMINI_API_KEY | Your Google AI Studio API key |
   | GROQ_API_KEY | Your Groq Console API key |
   | ADMIN_TOKEN | Your secure admin token |
   | PORT | 8000 |

5. **Deploy**
   
   Click "Create Web Service". Render will build and deploy your application.

   **Note**: The free tier has a cold start time of ~30 seconds. The first request after inactivity will take longer to respond as the service wakes up.

6. **Access your deployed app**
   
   Once deployed, Render will provide a URL like `https://nist-rag.onrender.com`. Use this URL to access your chat interface.

## API Reference

The application exposes three REST API endpoints:

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/api/ask` | Ask a question about NIST controls (streaming or non-streaming) | None |
| POST | `/api/ingest` | Manually re-trigger document ingestion | Bearer token required |
| GET | `/api/health` | Health check with vector database statistics | None |

### `/api/ask`

Ask a question and receive an answer with source citations.

**Request:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the requirements for access control policies?",
    "stream": false
  }'
```

**Streaming Request:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the auditing requirements in AC-2",
    "stream": true
  }'
```

**Response (non-streaming):**
```json
{
  "answer": "According to NIST 800-53, AC-2 requires that...",
  "sources": [
    {"control_id": "AC-2", "page": 12, "snippet": "The organization..."},
    {"control_id": "AC-2.1", "page": 13, "snippet": "The information system..."}
  ],
  "model": "llama-3.3-70b-versatile"
}
```

### `/api/ingest`

Manually trigger the ingestion pipeline to rebuild the vector database.

**Request:**
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "chunks_created": 1847,
  "duration_seconds": 45.2
}
```

### `/api/health`

Check application health and vector database status.

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "vector_count": 1847,
  "chroma_db_path": "./chroma_db",
  "models": {
    "embedding": "text-embedding-004",
    "llm": "llama-3.3-70b-versatile",
    "reranker": "ms-marco-MiniLM-L-6-v2"
  }
}
```

## Configuration Reference

Configure the application using environment variables in `.env` or your deployment platform.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google AI Studio API key for embeddings |
| `GROQ_API_KEY` | Yes | — | Groq Console API key for LLM inference |
| `ADMIN_TOKEN` | No | — | Bearer token for `/api/ingest` endpoint security |
| `CHROMA_DB_PATH` | No | `./chroma_db` | File path for ChromaDB persistent storage |
| `CHUNK_SIZE` | No | `800` | Maximum characters per document chunk |
| `CHUNK_OVERLAP` | No | `100` | Character overlap between chunks for context continuity |
| `RETRIEVAL_K` | No | `6` | Number of chunks retrieved before reranking |
| `RERANK_TOP_N` | No | `3` | Number of chunks passed to LLM after reranking |
| `MAX_TOKENS` | No | `512` | Maximum tokens in LLM response |
| `TEMPERATURE` | No | `0.1` | LLM temperature (lower = more deterministic) |

## Extending This Project

The modular architecture makes it easy to extend this compliance assistant:

- **Multi-Framework Support**: Add ISO 27001, SOC 2, or FedRAMP by dropping additional PDFs into the `data/` directory and re-running ingestion
- **Model Upgrades**: Swap Groq for GPT-4o by replacing `ChatGroq` with `ChatOpenAI` in `retrieval/chain.py`
- **User Authentication**: Add user management using FastAPI's `OAuth2PasswordBearer` for enterprise deployments
- **Multi-Tenant SaaS**: Replace ChromaDB with Pinecone or Weaviate for managed multi-tenancy
- **Feedback Loop**: Implement thumbs up/down buttons to log query quality and improve retrieval accuracy
- **Multimodal Ingestion**: Enable PDF diagram captioning using GPT-4o vision for richer context
- **Citations Export**: Add "Download as PDF" functionality for compliance audit trails
- **Conversation History**: Implement session persistence using Redis for multi-turn conversations

## Cost Breakdown

This application runs entirely on free tiers, making it cost-free for personal or small-scale use:

| Component | Service | Cost (Monthly) |
|-----------|---------|----------------|
| Embeddings | Google AI Studio text-embedding-004 | $0 (free tier: 1,500 requests/day) |
| LLM | Groq llama-3.3-70b-versatile | $0 (free tier: unlimited for personal use) |
| Vector Database | ChromaDB (local) | $0 (self-hosted) |
| Reranker | HuggingFace model (local) | $0 (runs on CPU) |
| Hosting | Render.com Free Tier | $0 (512 MB RAM, 0.1 CPU) |
| **Total** | | **$0/month** |

**Free Tier Limits:**
- Google AI Studio: 1,500 embedding requests per day
- Groq: Rate-limited but generous for personal projects
- Render: Free tier includes 750 hours/month (sufficient for always-on)
- Cold starts: ~30 seconds wake-up time on Render free tier

## License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.