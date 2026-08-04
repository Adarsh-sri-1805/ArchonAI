from pathlib import Path


class Settings:

    # ==========================
    # Project Paths
    # ==========================

    BASE_DIR = Path(__file__).resolve().parent.parent

    UPLOAD_DIR = BASE_DIR / "uploads"

    DATA_DIR = BASE_DIR / "data"

    DATA_DIR.mkdir(exist_ok=True)

    FAISS_INDEX_PATH = DATA_DIR / "faiss.index"

    DOCUMENTS_PATH = DATA_DIR / "documents.pkl"

    # ==========================
    # Embedding
    # ==========================

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    EMBEDDING_DIMENSION = 384

    # ==========================
    # Chunking
    # ==========================

    CHUNK_SIZE = 1000

    CHUNK_OVERLAP = 200

    # ==========================
    # Retrieval
    # ==========================

    TOP_K = 5

    # ==========================
    # LLM
    # ==========================

    GEMINI_MODEL = "gemini-3.6-flash"

    # ==========================
    # Retrieval
    # ==========================

    TOP_K = 5

    SIMILARITY_THRESHOLD = 0.5

settings = Settings()