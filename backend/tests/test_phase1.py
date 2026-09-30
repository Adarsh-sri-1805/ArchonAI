import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import List

from src.core.config import settings
from src.domain.models import Base, KnowledgeBase, Document, DocumentChunk
from src.domain.schemas import (
    KnowledgeBaseCreate,
    DocumentCreate,
    DocumentChunkCreate,
    KnowledgeBaseResponse,
    DocumentResponse,
    DocumentChunkResponse,
)
from src.infrastructure.db import (
    init_central_db,
    get_central_db,
    get_partition_db,
    _partition_engines,
    _partition_sessionmakers,
    _lock,
)
from src.infrastructure.llm.embedding_providers import (
    EmbeddingProvider,
    SentenceTransformerProvider,
    build_embedding_provider,
)
from src.infrastructure.vector_store import FAISSVectorStoreProvider
from src.services.embedding_service import EmbeddingService


class MockEmbeddingProvider(EmbeddingProvider):
    """
    A lightweight mock embedding provider for deterministic testing.
    """

    @property
    def dimension(self) -> int:
        return 3

    def embed_query(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class TestPhase1StorageAndVector(unittest.TestCase):

    def setUp(self):
        # Create a unique temporary directory for this test run
        self.test_dir = tempfile.mkdtemp()
        self.storage_root = Path(self.test_dir) / "storage"
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Store original settings to restore them in tearDown
        self.original_storage_root = settings.STORAGE_ROOT
        self.original_central_db_url = settings.CENTRAL_DB_URL

        # Override configurations to use the test paths
        settings.STORAGE_ROOT = self.storage_root
        settings.CENTRAL_DB_URL = f"sqlite:///{self.storage_root.as_posix()}/central.db"

        # Dynamically re-bind the central engine and sessionmaker in the db module
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import src.infrastructure.db as db_mod

        self.original_engine = db_mod.central_engine
        self.original_sessionmaker = db_mod.CentralSessionLocal

        db_mod.central_engine = create_engine(
            settings.CENTRAL_DB_URL,
            connect_args={"check_same_thread": False}
        )
        db_mod.CentralSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=db_mod.central_engine
        )

        # Re-initialize central database tables
        db_mod.init_central_db()

    def tearDown(self):
        # Clear partition engine caches to release database file locks on Windows
        with _lock:
            _partition_engines.clear()
            _partition_sessionmakers.clear()

        # Restore db module variables
        import src.infrastructure.db as db_mod
        db_mod.central_engine = self.original_engine
        db_mod.CentralSessionLocal = self.original_sessionmaker

        # Restore settings
        settings.STORAGE_ROOT = self.original_storage_root
        settings.CENTRAL_DB_URL = self.original_central_db_url

        # Clean up temporary directories
        try:
            shutil.rmtree(self.test_dir)
        except Exception:
            pass

    # ── 1. Config tests ───────────────────────────────────────────────────────

    def test_config_paths(self):
        self.assertEqual(settings.STORAGE_ROOT, self.storage_root)
        self.assertTrue(settings.CENTRAL_DB_URL.endswith("central.db"))

    # ── 2. Central DB tests ───────────────────────────────────────────────────

    def test_central_db_operations(self):
        # Obtain session
        session_gen = get_central_db()
        db = next(session_gen)

        try:
            # Create a new Knowledge Base metadata record
            kb_data = KnowledgeBaseCreate(
                id="kb-test-123",
                name="Test KB",
                description="A test knowledge base description"
            )
            
            db_kb = KnowledgeBase(
                id=kb_data.id,
                name=kb_data.name,
                description=kb_data.description
            )
            db.add(db_kb)
            db.commit()
            db.refresh(db_kb)

            # Validate serialization schema
            kb_resp = KnowledgeBaseResponse.model_validate(db_kb)
            self.assertEqual(kb_resp.id, "kb-test-123")
            self.assertEqual(kb_resp.name, "Test KB")
            self.assertIsNotNone(kb_resp.created_at)

            # Read back from database
            retrieved = db.query(KnowledgeBase).filter(KnowledgeBase.id == "kb-test-123").first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.name, "Test KB")

        finally:
            try:
                next(session_gen)
            except StopIteration:
                pass

    # ── 3. Dynamic Partition DB tests ─────────────────────────────────────────

    def test_partitioned_db_operations(self):
        kb_id_a = "kb-a"
        kb_id_b = "kb-b"

        # Verify partitions are isolated and dynamically initialized
        with get_partition_db(kb_id_a) as db_a:
            # Add a document to partition A
            doc_a = Document(
                filename="doc_a.txt",
                content="This is the content of document A",
                metadata_json={"source": "upload"}
            )
            db_a.add(doc_a)
            db_a.commit()
            db_a.refresh(doc_a)

            # Add a chunk to document A
            chunk_a = DocumentChunk(
                document_id=doc_a.id,
                content="This is chunk A",
                vector_id=42,
                metadata_json={"index": 0}
            )
            db_a.add(chunk_a)
            db_a.commit()
            db_a.refresh(chunk_a)

            self.assertEqual(doc_a.id, 1)
            self.assertEqual(chunk_a.id, 1)

            # Validate schemas
            doc_resp = DocumentResponse.model_validate(doc_a)
            self.assertEqual(doc_resp.filename, "doc_a.txt")
            
            chunk_resp = DocumentChunkResponse.model_validate(chunk_a)
            self.assertEqual(chunk_resp.content, "This is chunk A")
            self.assertEqual(chunk_resp.vector_id, 42)

        # Check partition B is clean and completely isolated from partition A
        with get_partition_db(kb_id_b) as db_b:
            docs_in_b = db_b.query(Document).all()
            self.assertEqual(len(docs_in_b), 0)

            # Add a document in partition B
            doc_b = Document(
                filename="doc_b.txt",
                content="This is document B",
                metadata_json={}
            )
            db_b.add(doc_b)
            db_b.commit()
            db_b.refresh(doc_b)
            self.assertEqual(doc_b.id, 1)  # Auto-increment starts at 1 in partition B as well

        # Verify cascade deletes in partition A
        with get_partition_db(kb_id_a) as db_a:
            doc = db_a.query(Document).first()
            self.assertIsNotNone(doc)
            self.assertEqual(len(doc.chunks), 1)

            # Delete the document and confirm chunk cascaded
            db_a.delete(doc)
            db_a.commit()

            chunks_left = db_a.query(DocumentChunk).all()
            self.assertEqual(len(chunks_left), 0)

        # Confirm DB file paths exist
        self.assertTrue((self.storage_root / kb_id_a / "partition.db").exists())
        self.assertTrue((self.storage_root / kb_id_b / "partition.db").exists())

    # ── 4. Embedding Service & Provider tests ─────────────────────────────────

    def test_mock_embedding_service(self):
        mock_provider = MockEmbeddingProvider()
        service = EmbeddingService(provider=mock_provider)

        self.assertEqual(service.dimension, 3)
        self.assertEqual(service.embed_query("hello"), [0.1, 0.2, 0.3])
        self.assertEqual(
            service.embed_documents(["hello", "world"]),
            [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
        )

    def test_sentence_transformer_provider_lazy_loading(self):
        provider = SentenceTransformerProvider(model_name="all-MiniLM-L6-v2")
        service = EmbeddingService(provider=provider)

        # Dimension should match MiniLM (384)
        self.assertEqual(service.dimension, 384)

        # Generate actual embeddings (uses internet/local cache for the model)
        query_vector = service.embed_query("What is Archon AI?")
        self.assertEqual(len(query_vector), 384)
        
        doc_vectors = service.embed_documents(["First doc chunk.", "Second doc chunk."])
        self.assertEqual(len(doc_vectors), 2)
        self.assertEqual(len(doc_vectors[0]), 384)

    # ── 5. Vector Store Adapter tests ─────────────────────────────────────────

    def test_vector_store_adapter(self):
        kb_id = "kb-vector-test"
        dimension = 3
        vector_store = FAISSVectorStoreProvider(
            storage_root=str(self.storage_root),
            dimension=dimension
        )

        # Test index creation
        vector_store.create_index(kb_id, dimension)
        self.assertTrue((self.storage_root / kb_id / "vector.index").exists())

        # Test adding vectors
        vectors = [
            [1.0, 0.0, 0.0],  # Vector 0
            [0.0, 1.0, 0.0],  # Vector 1
            [0.0, 0.0, 1.0],  # Vector 2
        ]
        ids = [100, 101, 102]
        vector_store.add_vectors(kb_id, vectors, ids)

        # Query vector: query [1.0, 0.1, 0.0] should match vector 0 (id 100) first
        results = vector_store.query_vector(kb_id, [1.0, 0.1, 0.0], top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], 100)  # ID 100 is closest
        self.assertGreater(results[0][1], results[1][1])  # Score of closest is greater

        # Test deletion
        vector_store.delete_vectors(kb_id, [100])
        results_after = vector_store.query_vector(kb_id, [1.0, 0.1, 0.0], top_k=2)
        # ID 100 should no longer be returned
        self.assertNotIn(100, [r[0] for r in results_after])


if __name__ == "__main__":
    unittest.main()
