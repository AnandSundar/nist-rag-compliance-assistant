from typing import List, AsyncIterator
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from config import settings


SYSTEM_PROMPT = """You are a helpful NIST 800-53 security compliance assistant. You explain security controls in clear, simple language.

IMPORTANT INSTRUCTIONS:
1. Answer ONLY using the information provided in the context below
2. If the answer is not in the context, say "I don't have that information in my knowledge base"
3. Use clear, conversational language - avoid technical jargon when possible
4. Format your response as follows:

**## Summary**
Start with a brief 1-2 sentence overview

**## Controls**
Use + for bullet points:
+ **Control ID**: Brief description
+ **Control ID**: Brief description

**## Key Points**
+ Important details or notes

5. When mentioning controls, always use bold format: **Control ID**
6. Keep descriptions concise - 1 line per control
7. Don't repeat "no details available" - just list the control ID
8. Group related controls together

Context:
{context}

Question: {question}

Provide a clear, user-friendly response:"""


def format_docs(docs: List[Document]) -> str:
    formatted = []
    for i, doc in enumerate(docs, 1):
        control_id = doc.metadata.get("control_id", "Unknown")
        formatted.append(
            f"[Source {i} - Control: {control_id}]\n{doc.page_content.strip()}"
        )
    return "\n\n---\n\n".join(formatted)


def create_rag_chain():
    llm = ChatGroq(
        model=settings.llm_model,
        api_key=settings.groq_api_key,
        temperature=0.1
    )

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    chain = (
        RunnablePassthrough.assign(context=lambda x: format_docs(x["context"]))
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def invoke_chain(question: str, docs: List[Document]) -> str:
    chain = create_rag_chain()
    response = chain.invoke({"question": question, "context": docs})
    return response


async def astream_chain(question: str, docs: List[Document]) -> AsyncIterator[str]:
    chain = create_rag_chain()
    async for token in chain.astream({"question": question, "context": docs}):
        yield token
