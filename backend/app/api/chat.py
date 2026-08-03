from fastapi import APIRouter, HTTPException, Request

from app.services.llm import generate_response
from app.services.prompt_builder import build_prompt
from app.services.retriever import retrieve

router = APIRouter()


@router.post("/chat")
async def chat(
    request: Request,
    query: str,
):
    try:
        documents = retrieve(
            query=query,
            vector_store=request.app.state.vector_store,
        )

        prompt = build_prompt(
            query=query,
            documents=documents,
        )

        answer = generate_response(prompt)

        return {
            "query": query,
            "answer": answer,
            "sources": [
                document.metadata
                for document in documents
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )