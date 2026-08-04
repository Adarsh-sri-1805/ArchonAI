import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.logger import logger
from app.services.chunker import chunk_documents
from app.services.embedder import embed_documents
from app.services.parser import parse_document

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
):
    start = time.perf_counter()

    try:
        logger.info("Upload request received: %s", file.filename)

        file_path = UPLOAD_DIR / file.filename

        with open(file_path, "wb") as f:
            f.write(await file.read())

        logger.info("File saved: %s", file.filename)

        parse_start = time.perf_counter()

        documents = parse_document(file_path)

        logger.info(
            "Parsing completed in %.2fs",
            time.perf_counter() - parse_start,
        )

        chunk_start = time.perf_counter()

        documents = chunk_documents(documents)

        logger.info(
            "Chunking completed in %.2fs (%d chunks)",
            time.perf_counter() - chunk_start,
            len(documents),
        )

        embedding_start = time.perf_counter()

        embeddings = embed_documents(documents)

        logger.info(
            "Embeddings generated in %.2fs",
            time.perf_counter() - embedding_start,
        )

        request.app.state.vector_store.add(
            embeddings,
            documents,
        )

        request.app.state.bm25_store.add(
            documents,
        )

        logger.info(
            "Upload completed in %.2fs",
            time.perf_counter() - start,
        )

        return {
            "message": "File uploaded successfully",
            "chunks": len(documents),
        }

    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )