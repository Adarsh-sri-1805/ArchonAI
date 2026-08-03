import faiss
import numpy as np

from app.models.document import Document


class VectorStore:
    def __init__(self, embedding_dimension: int):
        self.index = faiss.IndexFlatIP(embedding_dimension)
        self.documents: list[Document] = []

    def add(
        self,
        embeddings: list[list[float]],
        documents: list[Document],
    ):
        vectors = np.array(embeddings, dtype="float32")

        self.index.add(vectors)
        self.documents.extend(documents)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ):
        query = np.array([query_embedding], dtype="float32")

        scores, indices = self.index.search(query, top_k)

        results = []

        for score, idx in zip(scores[0], indices[0]):

            if idx == -1:
                continue

            results.append(
                {
                    "document": self.documents[idx],
                    "score": float(score),
                }
            )

        return results