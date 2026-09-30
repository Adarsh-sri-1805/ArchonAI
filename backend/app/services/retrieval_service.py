"""
app/services/retrieval_service.py
-----------------------------------
RetrievalService — owns hybrid search (vector + BM25 → RRF → reranker).

This service knows about Chunks and scores.
It does NOT know about Git, repositories, embeddings internals,
or LLM generation.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.models.document import Document
from app.services.embedding_service import EmbeddingProvider
from app.services.vector_store_service import VectorStoreProvider
from app.services.bm25_store import BM25Store
from app.core.config import settings

logger = logging.getLogger("archon.retrieval")

DEFAULT_KB_ID = "default"


class RetrievalService:

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStoreProvider,
        bm25_store: BM25Store,
        kb_id: str = DEFAULT_KB_ID,
    ):
        self._embedding = embedding_provider
        self._vector_store = vector_store
        self._bm25 = bm25_store
        self._kb_id = kb_id

    # ── RRF fusion ────────────────────────────────────────────────────────────

    @staticmethod
    def _rrf(
        vector_results: List[Dict],
        bm25_results: List[Dict],
        k: int = 60,
    ) -> List[Dict]:
        fused: Dict[str, Dict] = {}

        for ranking in (vector_results, bm25_results):
            for rank, result in enumerate(ranking):
                doc = result["document"]
                key = doc.page_content  # identity by content
                if key not in fused:
                    fused[key] = {"document": doc, "score": 0.0}
                fused[key]["score"] += 1.0 / (k + rank + 1)

        return sorted(fused.values(), key=lambda x: x["score"], reverse=True)

    # ── Cross-encoder reranker ────────────────────────────────────────────────

    @staticmethod
    def _rerank(query: str, results: List[Dict], top_n: int) -> List[Dict]:
        from app.services.reranker import rerank
        return rerank(query=query, results=results, top_k=top_n)

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        rerank_enabled: bool = True,
    ) -> List[Dict]:
        """
        Hybrid retrieval:
          1. Embed query
          2. Vector search (FAISS)
          3. Lexical search (BM25)
          4. Reciprocal Rank Fusion
          5. Optional Cross-encoder reranker
        Returns a list of {"document": Document, "score": float}.
        """
        final_top_k = top_k or getattr(settings, "TOP_K", 5)
        vector_top_k = getattr(settings, "VECTOR_TOP_K", 50)
        lexical_top_k = getattr(settings, "LEXICAL_TOP_K", 50)

        # 1. Embed
        query_vec = self._embedding.embed_query(query)

        # 2. Vector search → resolve document objects by vector_id
        raw_vector = self._vector_store.query_vector(
            self._kb_id, query_vec, top_k=vector_top_k
        )
        vector_results = self._resolve_vector_results(raw_vector)

        # 3. Lexical search
        bm25_results = self._bm25.search(query=query, top_k=lexical_top_k)

        logger.info(
            "Candidates — vector: %d, bm25: %d",
            len(vector_results), len(bm25_results),
        )

        # 4. RRF fusion
        fused = self._rrf(vector_results, bm25_results)

        if not fused:
            return []

        # 5. Rerank if enabled (trim to top 15 candidates for sub-100ms response)
        if rerank_enabled:
            rerank_candidates = fused[:15]
            reranked = self._rerank(query, rerank_candidates, top_n=final_top_k)
        else:
            reranked = fused[:final_top_k]

        logger.info("Final retrieved chunks: %d", len(reranked))
        return reranked


    def _resolve_vector_results(
        self, raw: List[tuple]
    ) -> List[Dict]:
        """
        Map (vector_id, score) pairs back to Document objects via BM25Store
        (which holds the in-memory document list at the same index positions).
        This is the current MVP approach. In Phase 2 it will query the SQLite
        metadata DB instead.
        """
        results = []
        for vector_id, score in raw:
            doc = self._bm25.get_by_index(vector_id)
            if doc is not None:
                results.append({"document": doc, "score": score})
        return results
