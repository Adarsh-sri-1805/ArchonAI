import os
import pickle
from pathlib import Path
from typing import List, Tuple

# pyrefly: ignore [missing-import]
from rank_bm25 import BM25Okapi

# pyrefly: ignore [missing-import]
from src.core.config import settings

class BM25Store:
    """BM25 index storage per knowledge base.

    Stores the BM25 index as a pickle file under the partition folder:
        {STORAGE_ROOT}/{kb_id}/bm25/index.pkl
    Configurable via environment variables BM25_K1 and BM25_B.
    """

    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        self.storage_dir = settings.STORAGE_ROOT / kb_id / "bm25"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage_dir / "index.pkl"
        self.k1 = float(os.getenv("BM25_K1", "1.5"))
        self.b = float(os.getenv("BM25_B", "0.75"))
        self._documents: List[str] = []
        self._bm25: BM25Okapi | None = None
        self._load()

    def _load(self) -> None:
        if self.index_path.is_file():
            with open(self.index_path, "rb") as f:
                self._documents, self._bm25 = pickle.load(f)
        else:
            self._documents = []
            self._bm25 = None

    def _persist(self) -> None:
        with open(self.index_path, "wb") as f:
            pickle.dump((self._documents, self._bm25), f)

    def add_documents(self, texts: List[str]) -> None:
        """Add a batch of document chunk texts to the BM25 index."""
        self._documents.extend(texts)
        tokenized = [doc.split() for doc in self._documents]
        self._bm25 = BM25Okapi(tokenized, k1=self.k1, b=self.b)
        self._persist()

    def query(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """Return a list of (doc_index, score) for the top_k matching documents."""
        if not self._bm25:
            return []
        tokens = query.split()
        scores = self._bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(i, scores[i]) for i in top_indices]
