import hashlib
from typing import List
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings


def generate_id(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def embed_and_store(documents: List[Document]) -> None:
    client = chromadb.PersistentClient(path=settings.chroma_db_path)

    existing_collections = client.list_collections()
    collection_exists = any(c.name == settings.chroma_collection_name for c in existing_collections)

    if collection_exists:
        collection = client.get_collection(name=settings.chroma_collection_name)
        count = collection.count()
        if count > 0:
            print(f"Index already exists with {count} documents, skipping ingestion")
            return

    print(f"Creating new collection '{settings.chroma_collection_name}'...")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    from langchain_chroma import Chroma
    vectorstore = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        client=client,
        persist_directory=settings.chroma_db_path
    )

    batch_size = 50
    total_docs = len(documents)

    ids = [generate_id(doc.page_content) for doc in documents]

    for i in range(0, total_docs, batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]

        vectorstore.add_documents(documents=batch_docs, ids=batch_ids)

        processed = min(i + batch_size, total_docs)
        print(f"Processed {processed}/{total_docs} chunks...")

    collection = client.get_collection(name=settings.chroma_collection_name)
    final_count = collection.count()
    print(f"Ingestion complete! Total vectors in database: {final_count}")
