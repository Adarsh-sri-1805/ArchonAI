import pickle

import faiss
import numpy as np

from app.core.config import settings
from app.core.logger import logger
from app.models.document import Document


class VectorStore:

    def __init__(self, embedding_dimension: int):

        self.index = faiss.IndexFlatIP(
            embedding_dimension
        )

        self.documents: list[Document] = []

    def add(
        self,
        embeddings: list[list[float]],
        documents: list[Document],
    ):

        vectors = np.array(
            embeddings,
            dtype="float32",
        )

        self.index.add(vectors)

        self.documents.extend(documents)

        logger.info(
            "Added %d documents to vector store",
            len(documents),
        )

        self.save()

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ):

        query = np.array(
            [query_embedding],
            dtype="float32",
        )

        scores, indices = self.index.search(
            query,
            top_k,
        )

        results = []

        for score, idx in zip(
            scores[0],
            indices[0],
        ):

            if idx == -1:
                continue

            results.append(
                {
                    "document": self.documents[idx],
                    "score": float(score),
                }
            )

        logger.info(
            "Retrieved %d document(s)",
            len(results),
        )

        return results

    def save(self):

        logger.info("Saving vector store...")

        faiss.write_index(
            self.index,
            str(settings.FAISS_INDEX_PATH),
        )

        with open(
            settings.DOCUMENTS_PATH,
            "wb",
        ) as file:

            pickle.dump(
                self.documents,
                file,
            )

        logger.info(
            "Vector store saved successfully (%d documents)",
            len(self.documents),
        )

    def load(self):

        logger.info("Loading vector store...")

        if settings.FAISS_INDEX_PATH.exists():

            self.index = faiss.read_index(
                str(settings.FAISS_INDEX_PATH)
            )

            logger.info("FAISS index loaded.")

        else:

            logger.info("No FAISS index found. Starting fresh.")

        if settings.DOCUMENTS_PATH.exists():

            with open(
                settings.DOCUMENTS_PATH,
                "rb",
            ) as file:

                self.documents = pickle.load(file)

            logger.info(
                "Loaded %d documents from disk.",
                len(self.documents),
            )

        else:

            logger.info("No saved documents found. Starting fresh.")