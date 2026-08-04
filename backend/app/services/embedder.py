from app.core.config import settings
from app.models.document import Document

_model = None


def get_model():
    global _model

    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(
            settings.EMBEDDING_MODEL
        )

    return _model


def embed_documents(
    documents: list[Document],
) -> list[list[float]]:
    """
    Generate embeddings for multiple documents.
    """

    model = get_model()

    texts = [
        document.page_content
        for document in documents
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embeddings.tolist()


def embed_query(
    query: str,
) -> list[float]:
    """
    Generate embedding for a single query.
    """

    model = get_model()

    embedding = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embedding.tolist()