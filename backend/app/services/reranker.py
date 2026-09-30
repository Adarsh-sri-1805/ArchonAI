import logging
from sentence_transformers import CrossEncoder

logger = logging.getLogger("archon.reranker")

_model = None


def get_model():
    global _model
    if _model is None:
        logger.info("Initializing CrossEncoder reranker: cross-encoder/ms-marco-MiniLM-L-6-v2")
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _model


def warmup_reranker():
    """Pre-load weights and warm up inference engine on startup."""
    try:
        logger.info("Pre-warming CrossEncoder reranker...")
        model = get_model()
        _ = model.predict([("test query", "test content")], show_progress_bar=False)
        logger.info("CrossEncoder reranker ready in memory.")
    except Exception as e:
        logger.warning("Reranker warmup error: %s", e)


def rerank(query: str, results: list[dict], top_k: int = 5):
    """
    Rerank retrieved documents using a Cross Encoder.
    """
    if not results:
        return []

    model = get_model()

    pairs = [
        (
            query,
            result["document"].page_content,
        )
        for result in results
    ]

    scores = model.predict(pairs, batch_size=32, show_progress_bar=False)

    reranked = []
    for result, score in zip(results, scores):
        reranked.append(
            {
                "document": result["document"],
                "score": float(score),
            }
        )

    reranked.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return reranked[:top_k]