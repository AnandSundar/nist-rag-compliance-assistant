from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import chromadb
from langchain_core.documents import Document
import json

from config import settings
from retrieval.retriever import get_retriever, rerank, get_reranker
from retrieval.chain import astream_chain, invoke_chain


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="The question to ask")
    stream: bool = Field(default=True, description="Whether to stream the response")


class AskResponse(BaseModel):
    answer: str
    sources: List[dict]


class HealthResponse(BaseModel):
    status: str
    collection_count: int
    model: str


class IngestResponse(BaseModel):
    status: str
    chunks_processed: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading CrossEncoder model...")
    get_reranker()
    print("Application startup complete")
    yield
    print("Application shutdown")


app = FastAPI(
    title="NIST 800-53 Compliance Assistant",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health():
    try:
        client = chromadb.PersistentClient(path=settings.chroma_db_path)
        collection = client.get_collection(name=settings.chroma_collection_name)
        count = collection.count()
        return HealthResponse(
            status="ok",
            collection_count=count,
            model=settings.llm_model
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}"
        )


@app.post("/api/ask")
async def ask(request: AskRequest, http_request: Request):
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )

    question = request.question.strip()
    if len(question) > 500:
        question = question[:500]

    try:
        retriever = get_retriever()
        retrieved_docs = retriever.invoke(question)
        reranked_docs = rerank(question, retrieved_docs)

        sources = [
            {
                "text": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "control_id": doc.metadata.get("control_id", "Unknown")
            }
            for doc in reranked_docs
        ]

        if request.stream:
            async def generate():
                yield f"data: {json.dumps({'type': 'start', 'sources': sources})}\n\n"

                async for token in astream_chain(question, reranked_docs):
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

                yield f"data: {json.dumps({'type': 'end'})}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            answer = invoke_chain(question, reranked_docs)
            return AskResponse(answer=answer, sources=sources)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest(http_request: Request):
    auth_header = http_request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.split(" ")[1]
    if not settings.admin_token or token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )

    try:
        from ingestion.loader import load_pdf
        from ingestion.chunker import chunk_text
        from ingestion.embedder import embed_and_store

        text = load_pdf()
        documents = chunk_text(text)

        client = chromadb.PersistentClient(path=settings.chroma_db_path)
        collection = client.get_collection(name=settings.chroma_collection_name)
        collection.delete(where={})

        embed_and_store(documents)

        collection = client.get_collection(name=settings.chroma_collection_name)
        final_count = collection.count()

        return IngestResponse(status="success", chunks_processed=final_count)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )


try:
    import os
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
except Exception:
    pass
