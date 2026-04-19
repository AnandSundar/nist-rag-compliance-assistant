import re
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import settings


def chunk_text(text: str) -> List[Document]:
    nist_pattern = re.compile(r'\n([A-Z]{2}-\d+)\s')

    raw_chunks = nist_pattern.split(text)

    documents = []
    chunk_index = 0

    i = 1
    while i < len(raw_chunks):
        control_id = raw_chunks[i]
        content = raw_chunks[i + 1] if i + 1 < len(raw_chunks) else ""

        full_content = f"{control_id} {content}"

        if len(full_content) > settings.chunk_size:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            sub_chunks = splitter.split_text(full_content)
            for j, sub_chunk in enumerate(sub_chunks):
                if len(sub_chunk.strip()) >= 50:
                    doc = Document(
                        page_content=sub_chunk.strip(),
                        metadata={
                            "source": settings.pdf_path,
                            "control_id": control_id,
                            "chunk_index": chunk_index
                        }
                    )
                    documents.append(doc)
                    chunk_index += 1
        else:
            if len(full_content.strip()) >= 50:
                doc = Document(
                    page_content=full_content.strip(),
                    metadata={
                        "source": settings.pdf_path,
                        "control_id": control_id,
                        "chunk_index": chunk_index
                    }
                )
                documents.append(doc)
                chunk_index += 1

        i += 2

    print(f"Created {len(documents)} chunks using NIST-aware splitting")
    return documents
