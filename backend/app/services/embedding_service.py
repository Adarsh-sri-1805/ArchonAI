"""
app/services/embedding_service.py
-----------------------------------
EmbeddingProvider interface + concrete adapters.

RetrievalService and IndexingService depend ONLY on
the EmbeddingProvider ABC — never on a specific model.

To switch from SentenceTransformers to Gemini:
    set EMBEDDING_PROVIDER=gemini in .env
    No retrieval code changes required.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger("archon.embedding")


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

    def warmup(self) -> None:
        """Pre-warm model weights into memory."""
        try:
            self.embed_query("warmup")
        except Exception as e:
            logger.debug("Embedding warmup skipped: %s", e)


# ── SentenceTransformer adapter ───────────────────────────────────────────────

class SentenceTransformerProvider(EmbeddingProvider):
    """
    Optimized SentenceTransformer adapter with PyTorch multi-threading
    and fast batching.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None

    @property
    def _lazy_model(self):
        if self._model is None:
            try:
                import torch
                # Allocate CPU threads for fast parallel matrix operations
                num_cores = os.cpu_count() or 4
                torch.set_num_threads(max(2, min(8, num_cores)))
            except Exception:
                pass

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
        return 768 if "mpnet" in self._model_name else 384

    def warmup(self) -> None:
        try:
            logger.info("Pre-warming SentenceTransformer: %s", self._model_name)
            _ = self.embed_query("pre-warming model cache")
            logger.info("SentenceTransformer ready in memory.")
        except Exception as e:
            logger.warning("SentenceTransformer warmup error: %s", e)

    def embed_query(self, text: str) -> List[float]:
        return self._lazy_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._lazy_model.encode(
            texts,
            batch_size=64,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
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
        genai.configure(api_key=api_key)
        self._genai = genai
        self._model = model

    @property
    def dimension(self) -> int:
        return 768

    @staticmethod
    def _normalize(vector: List[float]) -> List[float]:
        import math
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:
            return vector
        return [x / norm for x in vector]

    def embed_query(self, text: str) -> List[float]:
        result = self._genai.embed_content(
            model=self._model, contents=text, task_type="RETRIEVAL_QUERY"
        )
        return self._normalize(result["embedding"])

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        # Batch in chunks of 60 to prevent payload limits
        all_embeddings = []
        chunk_size = 60
        for i in range(0, len(texts), chunk_size):
            batch = texts[i:i + chunk_size]
            result = self._genai.embed_content(
                model=self._model, contents=batch, task_type="RETRIEVAL_DOCUMENT"
            )
            emb = result["embedding"]
            if batch and isinstance(emb[0], float):
                all_embeddings.append(self._normalize(emb))
            else:
                all_embeddings.extend([self._normalize(vec) for vec in emb])
        return all_embeddings


# ── Factory ───────────────────────────────────────────────────────────────────

def build_embedding_provider(
    provider: str,
    model: str,
    api_key: str = "",
) -> EmbeddingProvider:
    """
    Called once from app startup (or dependency injection).
    Returns the configured EmbeddingProvider implementation.
    """
    if provider == "gemini":
        return GeminiEmbeddingProvider(api_key=api_key, model=model)
    return SentenceTransformerProvider(model_name=model)
