from app.core.config import settings
from app.services.embedder import embed_query
from app.services.reranker import rerank

def reciprocal_rank_fusion(vector_results, bm25_results, k=60):
    """
    Fuse FAISS and BM25 rankings using Reciprocal Rank Fusion (RRF).
    """

    fused_scores = {}

    for ranking in [vector_results, bm25_results]:

        for rank, result in enumerate(ranking):

            document = result["document"]

            key = (
                document.page_content,
                tuple(sorted(document.metadata.items())),
            )

            if key not in fused_scores:
                fused_scores[key] = {
                    "document": document,
                    "score": 0.0,
                }

            fused_scores[key]["score"] += 1 / (k + rank + 1)

    return sorted(
        fused_scores.values(),
        key=lambda x: x["score"],
        reverse=True,
    )[: settings.TOP_K]


def retrieve(
    query: str,
    vector_store,
    bm25_store,
):
    query_embedding = embed_query(query)

    vector_results = vector_store.search(
        query_embedding=query_embedding,
        top_k=10,
    )

    bm25_results = bm25_store.search(
        query=query,
        top_k=10,
    )

    hybrid_results = reciprocal_rank_fusion(
        vector_results,
        bm25_results,
    )

    return rerank(
        query=query,
        results=hybrid_results,
        top_k=settings.TOP_K,
    )