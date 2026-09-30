from __future__ import annotations

import logging
from typing import List, Dict, Any

from src.core.config import settings
from src.domain.models import Document as DBDocument, DocumentChunk as DBChunk
from src.domain.schemas import Document as SchemaDocument
from src.infrastructure.db import get_partition_db
from src.services.embedding_service import EmbeddingService
from src.infrastructure.vector_store import FAISSVectorStoreProvider, VectorStoreProvider
from src.services.bm25_store import BM25Store

logger = logging.getLogger(__name__)


class PersistenceService:
    """Service responsible for persisting ingestion artifacts.

    Handles:
    * Knowledge source metadata (placeholder for future phases)
    * Full-file documents
    * Chunk documents – generating embeddings, storing them in the vector store
      and updating the BM25 index.
    """

    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        # Embedding service (uses global settings by default)
        self._embedding_service = EmbeddingService()
        # Vector store – using FAISS implementation
        self._vector_store: VectorStoreProvider = FAISSVectorStoreProvider(
            storage_root=str(settings.STORAGE_ROOT), dimension=settings.EMBEDDING_DIMENSION
        )
        # Ensure an index exists for this knowledge base
        self._vector_store.create_index(kb_id, settings.EMBEDDING_DIMENSION)
        # BM25 store – on-disk per-KB index (requires kb_id)
        self._bm25_store = BM25Store(kb_id=kb_id)

    # -------------------------------------------------------------------------
    # Knowledge source (currently a no-op placeholder)
    # -------------------------------------------------------------------------
    def persist_knowledge_source(self, source_meta: Dict[str, Any]) -> bool:
        logger.debug("Persist knowledge source meta: %s", source_meta)
        # Future phases may store this in a dedicated table.
        return True

    # -------------------------------------------------------------------------
    # File persistence
    # -------------------------------------------------------------------------
    def persist_file(self, file_doc: SchemaDocument) -> DBDocument:
        """Persist a whole-file document and return the ORM instance."""
        with get_partition_db(self.kb_id) as session:
            db_doc = DBDocument(
                filename=file_doc.metadata.get("file", "unknown"),
                content=file_doc.page_content,
                metadata_json=file_doc.metadata,
            )
            session.add(db_doc)
            session.commit()
            session.refresh(db_doc)
            logger.debug("Persisted file %s with id %s", db_doc.filename, db_doc.id)
            return db_doc

    # -------------------------------------------------------------------------
    # Chunk persistence
    # -------------------------------------------------------------------------
    def persist_chunk(self, chunk: SchemaDocument) -> DBChunk:
        """Persist a chunk, generate its embedding and update stores.

        The vector ID is the primary-key of the ``DocumentChunk`` row –
        FAISS uses the supplied IDs directly.
        """
        # 1️⃣ Embed the chunk text
        embedding = self._embedding_service.embed_documents([chunk.page_content])[0]

        # 2️⃣ Persist the chunk row
        with get_partition_db(self.kb_id) as session:
            db_chunk = DBChunk(
                document_id=chunk.metadata.get("document_id"),
                content=chunk.page_content,
                metadata_json=chunk.metadata,
            )
            session.add(db_chunk)
            session.commit()
            session.refresh(db_chunk)

            # 3️⃣ Store the embedding – use DB chunk ID as vector ID
            self._vector_store.add_vectors(self.kb_id, [embedding], [db_chunk.id])
            db_chunk.vector_id = db_chunk.id
            session.add(db_chunk)
            session.commit()

            logger.debug(
                "Persisted chunk id %s (vector_id=%s)", db_chunk.id, db_chunk.vector_id
            )

        # 4️⃣ Update BM25 index with raw text
        self._bm25_store.add_documents([chunk.page_content])
        return db_chunk

    # -------------------------------------------------------------------------
    # Batch helpers
    # -------------------------------------------------------------------------
    def persist_documents(self, docs: List[SchemaDocument]) -> List[DBDocument]:
        return [self.persist_file(d) for d in docs]

    def persist_chunks(self, chunks: List[SchemaDocument]) -> List[DBChunk]:
        return [self.persist_chunk(c) for c in chunks]
