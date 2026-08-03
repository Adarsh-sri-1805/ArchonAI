from fastapi import APIRouter, HTTPException, Request

from app.services.embedder import embed_chunks

router = APIRouter()


@router.post("/search")
async def search(
    request: Request,
    query: str
):
    try:
        query_embedding = embed_chunks([query])[0]

        results = request.app.state.vector_store.search(
            query_embedding,
            top_k=5
        )

        return {
            "query": query,
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )