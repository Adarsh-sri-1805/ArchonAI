import re

from rank_bm25 import BM25Okapi


class BM25Store:
    def __init__(self):
        self.documents = []
        self.corpus = []
        self.bm25 = None

    def tokenize(self, text: str):
        """
        Lowercase and split text into clean word tokens.
        """
        return re.findall(r"\b\w+\b", text.lower())

    def add(self, documents):
        self.documents.extend(documents)

        self.corpus = [
            self.tokenize(doc.page_content)
            for doc in self.documents
        ]

        self.bm25 = BM25Okapi(self.corpus)

    def search(self, query: str, top_k: int = 10):
        if self.bm25 is None:
            return []

        query_tokens = self.tokenize(query)

        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        results = []

        for idx, score in ranked:
            results.append(
                {
                    "document": self.documents[idx],
                    "score": float(score),
                }
            )

        return results