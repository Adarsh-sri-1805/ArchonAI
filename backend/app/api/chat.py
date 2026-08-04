import time

from fastapi import APIRouter, HTTPException, Request

from app.core.logger import logger
from app.services.llm import generate_response
from app.services.prompt_builder import build_prompt
from app.services.retriever import retrieve

router = APIRouter()


@router.post("/chat")
async def chat(
    request: Request,
    query: str,
):
    start = time.perf_counter()

    try:
        logger.info("Chat request: %s", query)

        retrieval_start = time.perf_counter()

        results = retrieve(
            query=query,
            vector_store=request.app.state.vector_store,
            bm25_store=request.app.state.bm25_store,
        )

        logger.info(
            "Retrieved %d documents in %.2fs",
            len(results),
            time.perf_counter() - retrieval_start,
        )

        documents = [
            result["document"]
            for result in results
        ]

        prompt = build_prompt(
            query=query,
            documents=documents,
        )

        llm_start = time.perf_counter()

        answer = generate_response(prompt)

        logger.info(
            "LLM response generated in %.2fs",
            time.perf_counter() - llm_start,
        )

        logger.info(
            "Chat completed in %.2fs",
            time.perf_counter() - start,
        )

        return {
            "query": query,
            "answer": answer,
            "sources": [
                {
                    **result["document"].metadata,
                    "score": round(result["score"], 4),
                    "excerpt": (
                        result["document"].page_content[:200] + "..."
                        if len(result["document"].page_content) > 200
                        else result["document"].page_content
                    ),
                }
                for result in results
            ],
        }

    except Exception as e:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )