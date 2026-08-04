from sentence_transformers import CrossEncoder

_model = None


def get_model():
    global _model

    if _model is None:
        _model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    return _model


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

    scores = model.predict(pairs)

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