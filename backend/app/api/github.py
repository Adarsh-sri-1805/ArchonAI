import traceback

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.post("/github")
async def ingest_repository(
    request: Request,
    repo_url: str,
):
    """
    Clone (or pull) a GitHub repository and index all its source files.

    Delegates:
      * Git operations  → GitService   (app.state.git_service)
      * Parse + embed   → IndexingService (app.state.indexing_service)
    """
    try:
        # 1️⃣ Clone / pull the repo
        repo_path = request.app.state.git_service.sync(repo_url)

        # 2️⃣ Parse, chunk, embed and store every file
        chunks_indexed = request.app.state.indexing_service.index_repository(repo_path)

        return {
            "message": "Repository indexed successfully.",
            "repository": repo_path.name,
            "chunks_indexed": chunks_indexed,
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )