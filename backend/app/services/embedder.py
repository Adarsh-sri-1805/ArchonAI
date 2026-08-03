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
    Generate embeddings for a list of Documents.
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