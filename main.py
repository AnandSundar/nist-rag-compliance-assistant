import argparse
import asyncio
from config import settings
from ingestion.loader import load_pdf
from ingestion.chunker import chunk_text
from ingestion.embedder import embed_and_store
from retrieval.retriever import get_retriever, rerank
from retrieval.chain import invoke_chain


def run_ingestion():
    print("=" * 50)
    print("NIST 800-53 RAG - Ingestion Pipeline")
    print("=" * 50)

    print("\n[1/3] Loading PDF...")
    text = load_pdf()

    print("\n[2/3] Chunking text...")
    documents = chunk_text(text)

    print("\n[3/3] Embedding and storing...")
    embed_and_store(documents)

    print("\n✓ Ingestion complete!")


def run_test():
    print("=" * 50)
    print("NIST 800-53 RAG - Retrieval Test")
    print("=" * 50)

    test_question = "What is the purpose of AC-1?"
    print(f"\nQuestion: {test_question}")

    print("\n[1/3] Retrieving documents...")
    retriever = get_retriever()
    retrieved_docs = retriever.invoke(test_question)
    print(f"Retrieved {len(retrieved_docs)} documents")

    print("\n[2/3] Reranking...")
    reranked_docs = rerank(test_question, retrieved_docs)
    print(f"Reranked to top {len(reranked_docs)} documents")

    print("\n[3/3] Generating answer...")
    answer = invoke_chain(test_question, reranked_docs)

    print("\n" + "=" * 50)
    print("RETRIEVED CHUNKS:")
    print("=" * 50)
    for i, doc in enumerate(reranked_docs, 1):
        control_id = doc.metadata.get("control_id", "Unknown")
        print(f"\n[Chunk {i} - Control: {control_id}]")
        print(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)

    print("\n" + "=" * 50)
    print("ANSWER:")
    print("=" * 50)
    print(answer)
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="NIST 800-53 RAG Compliance Assistant")
    parser.add_argument("--ingest", action="store_true", help="Run ingestion pipeline")
    parser.add_argument("--test", action="store_true", help="Run retrieval test")
    args = parser.parse_args()

    if args.ingest:
        run_ingestion()
    elif args.test:
        run_test()
    else:
        print("Use --ingest to run ingestion or --test to run retrieval tests")
        print("Or run: uvicorn api.server:app --reload")


if __name__ == "__main__":
    main()
