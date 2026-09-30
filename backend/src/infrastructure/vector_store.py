from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from src.core.config import settings
from src.core.logger import logger


# ── Abstract interface ────────────────────────────────────────────────────────

class VectorStoreProvider(ABC):

    @abstractmethod
    def create_index(self, kb_id: str, dimension: int) -> None:
        """Initialise an isolated vector index for a Knowledge Base."""

    @abstractmethod
    def add_vectors(
        self, kb_id: str, vectors: List[List[float]], ids: List[int]
    ) -> None:
        """Add dense vectors mapped to integer metadata IDs."""

    @abstractmethod
    def query_vector(
        self, kb_id: str, query_vector: List[float], top_k: int
    ) -> List[Tuple[int, float]]:
        """Return top_k most similar (id, score) pairs."""

    @abstractmethod
    def delete_vectors(self, kb_id: str, ids: List[int]) -> None:
        """Remove vectors from the index by their metadata IDs."""

    @abstractmethod
    def persist(self, kb_id: str) -> None:
        """Flush in-memory index to disk."""


# ── FAISS adapter ─────────────────────────────────────────────────────────────

class FAISSVectorStoreProvider(VectorStoreProvider):
    """
    Stores one FAISS IndexIDMap per KB under:
        {storage_root}/{kb_id}/vector.index

    Uses a simple in-process dict as an LRU cache (max_cached).
    """

    DEFAULT_KB_ID = "default"

    def __init__(self, storage_root: str, dimension: int = 384, max_cached: int = 10):
        self._storage_root = storage_root
        self._dimension = dimension
        self._max_cached = max_cached
        self._cache: Dict[str, object] = {}  # kb_id -> faiss.IndexIDMap

    # ── helpers ───────────────────────────────────────────────────────────────

    def _index_path(self, kb_id: str) -> str:
        return os.path.join(self._storage_root, kb_id, "vector.index")

    def _load(self, kb_id: str):
        if kb_id in self._cache:
            # Refresh LRU position
            self._cache[kb_id] = self._cache.pop(kb_id)
            return self._cache[kb_id]

        try:
            import faiss  # type: ignore
        except ImportError:
            raise RuntimeError("faiss-cpu is not installed. Run: pip install faiss-cpu")

        path = self._index_path(kb_id)
        if os.path.exists(path):
            logger.info("Loading FAISS index for kb=%s from %s", kb_id, path)
            index = faiss.read_index(path)
        else:
            logger.info("Creating new FAISS index for kb=%s at %s", kb_id, path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            base = faiss.IndexFlatIP(self._dimension)
            index = faiss.IndexIDMap(base)
            faiss.write_index(index, path)

        # Evict least recently used entry if over capacity
        if len(self._cache) >= self._max_cached:
            evicted = next(iter(self._cache))
            logger.debug("LRU evict: kb=%s", evicted)
            del self._cache[evicted]

        self._cache[kb_id] = index
        return index

    # ── public interface ──────────────────────────────────────────────────────

    def create_index(self, kb_id: str, dimension: int) -> None:
        self._dimension = dimension
        self._load(kb_id)

    def add_vectors(
        self, kb_id: str, vectors: List[List[float]], ids: List[int]
    ) -> None:
        import faiss
        import numpy as np

        if not vectors or not ids:
            return

        index = self._load(kb_id)
        index.add_with_ids(
            np.array(vectors, dtype="float32"),
            np.array(ids, dtype="int64"),
        )
        self.persist(kb_id)

    def query_vector(
        self, kb_id: str, query_vector: List[float], top_k: int
    ) -> List[Tuple[int, float]]:
        import numpy as np

        index = self._load(kb_id)
        scores, indices = index.search(
            np.array([query_vector], dtype="float32"), top_k
        )
        return [
            (int(idx), float(score))
            for idx, score in zip(indices[0], scores[0])
            if idx != -1
        ]

    def delete_vectors(self, kb_id: str, ids: List[int]) -> None:
        import numpy as np

        if not ids:
            return

        index = self._load(kb_id)
        if hasattr(index, "remove_ids"):
            index.remove_ids(np.array(ids, dtype="int64"))
            self.persist(kb_id)

    def persist(self, kb_id: str) -> None:
        import faiss

        if kb_id in self._cache:
            faiss.write_index(self._cache[kb_id], self._index_path(kb_id))
