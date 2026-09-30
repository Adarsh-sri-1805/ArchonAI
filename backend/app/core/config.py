"""
app/core/config.py
------------------
Central configuration using pydantic-settings.
All values can be overridden via environment variables or a .env file.
"""
import os
from pathlib import Path
from typing import Literal, Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _USE_PYDANTIC_SETTINGS = True
except ImportError:
    # Fallback if pydantic-settings is not installed yet
    _USE_PYDANTIC_SETTINGS = False


if _USE_PYDANTIC_SETTINGS:
    class Settings(BaseSettings):

        # ── Project ────────────────────────────────────────────────────────
        PROJECT_NAME: str = "Archon AI"

        # ── Paths ──────────────────────────────────────────────────────────
        BASE_DIR: Path = Path(__file__).resolve().parent.parent
        UPLOAD_DIR: Path = BASE_DIR / "uploads"
        STORAGE_ROOT: Path = BASE_DIR / "storage"   # workspace-scoped indexes live here
        GIT_CLONE_ROOT: Path = BASE_DIR / "repositories"

        # ── Embedding ──────────────────────────────────────────────────────
        # "sentence_transformer" | "gemini"
        EMBEDDING_PROVIDER: Literal["sentence_transformer", "gemini"] = "sentence_transformer"
        EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
        EMBEDDING_DIMENSION: int = 384

        # ── Chunking ───────────────────────────────────────────────────────
        CHUNK_SIZE: int = 1000
        CHUNK_OVERLAP: int = 200

        # ── Retrieval ──────────────────────────────────────────────────────
        TOP_K: int = 5
        VECTOR_TOP_K: int = 50       # candidates from vector search before RRF
        LEXICAL_TOP_K: int = 50      # candidates from BM25 before RRF
        SIMILARITY_THRESHOLD: float = 0.5

        # ── LLM ────────────────────────────────────────────────────────────
        # "fallback" | "gemini" | "groq" | "openai"
        CHAT_PROVIDER: Literal["fallback", "gemini", "groq", "openai", "gemini+groq", "auto"] = "fallback"
        GEMINI_API_KEY: str = ""
        GEMINI_MODEL: str = "gemini-2.0-flash"
        GROQ_API_KEY: str = ""
        GROQ_MODEL: str = "llama-3.3-70b-versatile"
        OPENAI_API_KEY: str = ""
        OPENAI_MODEL: str = "gpt-4o"

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )

        def model_post_init(self, __context):
            # Ensure storage directories exist on first import
            self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            self.STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
            self.GIT_CLONE_ROOT.mkdir(parents=True, exist_ok=True)

else:
    # Minimal fallback (no pydantic-settings installed)
    class Settings:  # type: ignore
        PROJECT_NAME = "Archon AI"
        BASE_DIR = Path(__file__).resolve().parent.parent
        UPLOAD_DIR = BASE_DIR / "uploads"
        STORAGE_ROOT = BASE_DIR / "storage"
        GIT_CLONE_ROOT = BASE_DIR / "repositories"
        EMBEDDING_PROVIDER = "sentence_transformer"
        EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        EMBEDDING_DIMENSION = 384
        CHUNK_SIZE = 1000
        CHUNK_OVERLAP = 200
        TOP_K = 5
        VECTOR_TOP_K = 50
        LEXICAL_TOP_K = 50
        SIMILARITY_THRESHOLD = 0.5
        CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "gemini")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        OPENAI_MODEL = "gpt-4o"

        def __init__(self):
            self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            self.STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
            self.GIT_CLONE_ROOT.mkdir(parents=True, exist_ok=True)


settings = Settings()