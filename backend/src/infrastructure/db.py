import os
import threading
from contextlib import contextmanager
from typing import Generator, Dict
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from src.core.config import settings
from src.domain.models import Base, KnowledgeBase, Document, DocumentChunk

# Thread lock for thread-safe engine creation
_lock = threading.Lock()

# Global caches for partition database engines and sessionmakers
_partition_engines: Dict[str, Engine] = {}
_partition_sessionmakers: Dict[str, sessionmaker] = {}

# ── Central Database Setup ───────────────────────────────────────────────────

# Configure connection args for SQLite to allow multi-thread access in dev.
# CENTRAL_DB_URL may be None if the settings object has not yet run post_init
# (e.g. when pydantic-settings is not installed and the fallback class is used).
_central_db_url = settings.CENTRAL_DB_URL or f"sqlite:///{settings.STORAGE_ROOT.as_posix()}/central.db"
connect_args = {"check_same_thread": False} if _central_db_url.startswith("sqlite") else {}

central_engine = create_engine(
    _central_db_url,
    connect_args=connect_args
)

CentralSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=central_engine
)


def init_central_db() -> None:
    """
    Initialises the central database schema.
    Creates only the tables relevant to the central database context.
    """
    Base.metadata.create_all(bind=central_engine, tables=[KnowledgeBase.__table__])


def get_central_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency / generator yielding a central database session.
    """
    db = CentralSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Partition Database Setup ─────────────────────────────────────────────────

@contextmanager
def get_partition_db(kb_id: str) -> Generator[Session, None, None]:
    """
    Context manager yielding a session to a dynamic workspace-specific partition database.
    Caches database engines and sessionmakers by kb_id for efficiency.
    Auto-creates the Document and DocumentChunk tables in the partition if they don't exist.
    """
    global _partition_engines, _partition_sessionmakers

    # Clean the kb_id to avoid path traversal
    safe_kb_id = "".join(c for c in kb_id if c.isalnum() or c in ("-", "_")).strip()
    if not safe_kb_id:
        raise ValueError(f"Invalid knowledge base ID: {kb_id}")

    with _lock:
        if safe_kb_id not in _partition_engines:
            # Resolve directory for workspace partition
            kb_dir = settings.STORAGE_ROOT / safe_kb_id
            kb_dir.mkdir(parents=True, exist_ok=True)
            db_path = kb_dir / "partition.db"
            db_url = f"sqlite:///{db_path.as_posix()}"

            # Create engine and sessionmaker
            engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False}
            )
            
            # Ensure partition tables are created
            Base.metadata.create_all(
                bind=engine,
                tables=[Document.__table__, DocumentChunk.__table__]
            )

            session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )

            _partition_engines[safe_kb_id] = engine
            _partition_sessionmakers[safe_kb_id] = session_factory

        session_factory = _partition_sessionmakers[safe_kb_id]

    session = session_factory()
    try:
        yield session
    finally:
        session.close()
