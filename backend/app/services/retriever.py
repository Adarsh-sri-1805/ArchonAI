from app.core.config import settings
from app.models.document import Document
from app.services.embedder import embed_documents
from app.services.vector_store import VectorStore


def retrieve(
    query: str,
    vector_store: VectorStore,
    top_k: int | None = None,
) -> list[Document]:
    """
    Retrieve the most relevant documents for a query.
    """

    if top_k is None:
        top_k = settings.TOP_K

    query_document = Document(
        page_content=query
    )

    query_embedding = embed_documents(
        [query_document]
    )[0]

    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=top_k,
    )

    documents = [
        result["document"]
        for result in results
    ]

    return documents