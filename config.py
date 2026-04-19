from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    groq_api_key: str
    chroma_db_path: str = "./chroma_db"
    chroma_collection_name: str = "nist_800_53"
    pdf_path: str = "./data/nist.pdf"
    embedding_model: str = "models/text-embedding-004"
    llm_model: str = "llama-3.3-70b-versatile"
    chunk_size: int = 800
    chunk_overlap: int = 150
    retrieval_k: int = 6
    rerank_top_n: int = 3
    admin_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
