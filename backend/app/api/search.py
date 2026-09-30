from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.post("/search")
def search(
    request: Request,
    query: str,
):
    """
    Hybrid search endpoint.
    Delegates to RetrievalService (vector + BM25 + RRF + reranker).
    Runs synchronously in threadpool to keep FastAPI event loop responsive.
    """
    try:
        results = request.app.state.retrieval_service.retrieve(query=query)

        return {
            "query": query,
            "results": [
                {
                    "score": round(result["score"], 4),
                    "excerpt": (
                        result["document"].page_content[:300] + "..."
                        if len(result["document"].page_content) > 300
                        else result["document"].page_content
                    ),
                    **result["document"].metadata,
                }
                for result in results
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )