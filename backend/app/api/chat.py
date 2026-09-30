import time

from fastapi import APIRouter, HTTPException, Request

from app.core.logger import logger
from app.services.prompt_builder import build_prompt

router = APIRouter()


@router.post("/chat")
def chat(
    request: Request,
    query: str,
):
    start = time.perf_counter()

    try:
        logger.info("Chat request: %s", query)

        retrieval_start = time.perf_counter()

        # 1️⃣ Hybrid retrieval via RetrievalService
        settings_service = getattr(request.app.state, "settings_service", None)
        cfg = settings_service._current_config if settings_service else {}
        top_k = int(cfg.get("top_k", 5))
        rerank_enabled = bool(cfg.get("rerank_enabled", True))

        results = request.app.state.retrieval_service.retrieve(
            query=query,
            top_k=top_k,
            rerank_enabled=rerank_enabled,
        )

        logger.info(
            "Retrieved %d documents in %.2fs",
            len(results),
            time.perf_counter() - retrieval_start,
        )

        documents = [result["document"] for result in results]

        # 2️⃣ Build prompt with rich metadata and call LLM
        prompt = build_prompt(query=query, documents=documents)

        llm_start = time.perf_counter()

        answer = request.app.state.llm_provider.generate(prompt)

        logger.info(
            "LLM response generated in %.2fs",
            time.perf_counter() - llm_start,
        )

        logger.info("Chat completed in %.2fs", time.perf_counter() - start)

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