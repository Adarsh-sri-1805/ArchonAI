from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.core.config import settings
from src.core.logger import logger


# ── Abstract interface ────────────────────────────────────────────────────────

class EmbeddingProvider(ABC):

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Output vector dimension (e.g. 384 or 768)."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of document strings."""


# ── SentenceTransformer adapter ───────────────────────────────────────────────

class SentenceTransformerProvider(EmbeddingProvider):
    """
    Lazy-loads the model on first call so FastAPI startup stays instant.
    The model is held in memory for the process lifetime.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None  # loaded lazily

    @property
    def _lazy_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
            logger.info("Loading SentenceTransformer: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
        return self._model

    @property
    def dimension(self) -> int:
        if "mpnet" in self._model_name:
            return 768
        return 384

    def embed_query(self, text: str) -> List[float]:
        return self._lazy_model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        ).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._lazy_model.encode(
            texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True
        ).tolist()


# ── Gemini adapter ────────────────────────────────────────────────────────────

class GeminiEmbeddingProvider(EmbeddingProvider):

    def __init__(self, api_key: str, model: str = "models/text-embedding-004"):
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise RuntimeError(
                "google-generativeai not installed. "
                "Run: pip install google-generativeai"
            )
        if not api_key:
            raise ValueError("API key must be provided for GeminiEmbeddingProvider")
        genai.configure(api_key=api_key)
        self._genai = genai
        self._model = model

    @property
    def dimension(self) -> int:
        return 768

    def embed_query(self, text: str) -> List[float]:
        result = self._genai.embed_content(
            model=self._model, contents=text, task_type="RETRIEVAL_QUERY"
        )
        return result["embedding"]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        result = self._genai.embed_content(
            model=self._model, contents=texts, task_type="RETRIEVAL_DOCUMENT"
        )
        emb = result["embedding"]
        if isinstance(emb[0], float):
            return [emb]
        return emb


# ── Factory ───────────────────────────────────────────────────────────────────

def build_embedding_provider(
    provider: str,
    model: str,
    api_key: str = "",
) -> EmbeddingProvider:
    """
    Returns the configured EmbeddingProvider implementation.
    """
    if provider == "gemini":
        return GeminiEmbeddingProvider(api_key=api_key, model=model)
    return SentenceTransformerProvider(model_name=model)
