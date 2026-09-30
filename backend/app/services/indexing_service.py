"""
app/services/indexing_service.py
----------------------------------
IndexingService — the single orchestrator for document/repository ingestion.

Responsibilities:
  1. Receive a file path or repository path
  2. Delegate parsing to parser.py / code_parser.py
  3. Delegate chunking to chunker.py / code_chunker.py
  4. Delegate embedding to EmbeddingProvider
  5. Persist vectors to VectorStoreProvider
  6. Persist tokens to BM25Store

This service has NO knowledge of HTTP, requests, or FastAPI.
Routers call this service; they do not do the work themselves.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from app.models.document import Document
from app.services.embedding_service import EmbeddingProvider
from app.services.vector_store_service import VectorStoreProvider
from app.services.bm25_store import BM25Store

logger = logging.getLogger("archon.indexing")

# Default knowledge base used before workspace isolation is introduced
DEFAULT_KB_ID = "default"


class IndexingService:

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

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _embed_and_store(self, documents: List[Document]) -> int:
        """Embed documents and write to both vector store and BM25."""
        if not documents:
            return 0

        texts = [d.page_content for d in documents]
        embeddings = self._embedding.embed_documents(texts)

        # Use the current total count as the starting vector_id offset
        start_id = self._bm25.total_count()
        ids = list(range(start_id, start_id + len(documents)))

        self._vector_store.add_vectors(self._kb_id, embeddings, ids)
        self._bm25.add(documents)

        logger.info(
            "Indexed %d chunks into kb=%s (vector_ids %d–%d)",
            len(documents), self._kb_id, ids[0], ids[-1],
        )
        return len(documents)

    # ── Public API ────────────────────────────────────────────────────────────

    def index_file(self, file_path: Path) -> int:
        """
        Parse and index a single uploaded document file (PDF, DOCX, TXT, CSV).
        Returns the number of chunks indexed.
        """
        from app.services.parser import parse_document
        from app.services.chunker import chunk_documents

        logger.info("Indexing file: %s", file_path.name)
        raw_docs = parse_document(file_path)
        chunks = chunk_documents(raw_docs)
        return self._embed_and_store(chunks)

    def index_repository(self, repo_path: Path) -> int:
        """
        Parse and index a cloned Git repository.
        Returns the number of chunks indexed.
        """
        from app.services.code_parser import parse_repository
        from app.services.chunker import chunk_documents

        logger.info("Indexing repository: %s", repo_path.name)
        raw_docs = parse_repository(repo_path)
        # code_parser already produces AST-aware chunks;
        # chunk_documents applies text splitting only to non-code fallback chunks
        chunks = chunk_documents(raw_docs)
        return self._embed_and_store(chunks)
