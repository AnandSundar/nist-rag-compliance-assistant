from typing import List, Optional
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from config import settings

_reranker_model: Optional[CrossEncoder] = None


def get_reranker() -> CrossEncoder:
    global _reranker_model
    if _reranker_model is None:
        print("Loading CrossEncoder model...")
        _reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("CrossEncoder model loaded")
    return _reranker_model


def get_retriever():
    client = chromadb.PersistentClient(path=settings.chroma_db_path)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    vectorstore = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        client=client,
        persist_directory=settings.chroma_db_path
    )

    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "fetch_k": 20,
            "k": settings.retrieval_k,
            "lambda_mult": 0.7
        }
    )


def rerank(query: str, docs: List[Document]) -> List[Document]:
    if len(docs) <= settings.rerank_top_n:
        return docs

    reranker = get_reranker()

    pairs = [[query, doc.page_content] for doc in docs]
    scores = reranker.predict(pairs)

    scored_docs = list(zip(docs, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in scored_docs[:settings.rerank_top_n]]
