import re
from typing import List
from rank_bm25 import BM25Okapi


class BM25Store:
    def __init__(self):
        self.documents = []
        self.corpus = []
        self.bm25 = None

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize code and natural language text into clean word tokens,
        including camelCase and snake_case sub-tokens.
        """
        raw_words = re.findall(r"[a-zA-Z0-9_]+", text)
        tokens = set()
        for word in raw_words:
            tokens.add(word.lower())
            # Split snake_case
            parts = word.split("_")
            for part in parts:
                if part:
                    tokens.add(part.lower())
            # Split camelCase / PascalCase
            sub_words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)|[0-9]+", word)
            for sub in sub_words:
                if sub:
                    tokens.add(sub.lower())
        return list(tokens)


    def add(self, documents: List):
        if not documents:
            return

        self.documents.extend(documents)
        new_tokens = [self.tokenize(doc.page_content) for doc in documents]
        self.corpus.extend(new_tokens)

        self.bm25 = BM25Okapi(self.corpus)


    def total_count(self):
        return len(self.documents)

    def get_by_index(self, index: int):
        if index < 0 or index >= len(self.documents):
            return None
        return self.documents[index]

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