"""
app/api/upload.py
------------------
Upload endpoint – now delegates all heavy work to ``IndexingService``.
The router only validates the request and returns a tiny JSON response.
"""
from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.logger import logger
from app.services.indexing_service import IndexingService

router = APIRouter()

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    start = time.perf_counter()
    try:
        logger.info("Upload request received: %s", file.filename)
        upload_dir: Path = request.app.state.upload_dir  # set in lifespan or fallback
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logger.info("File saved: %s", file_path)

        # --------------- Delegation ----------------
        indexing: IndexingService = request.app.state.indexing_service
        chunks_indexed = indexing.index_file(file_path)
        # -------------------------------------------

        logger.info(
            "Upload completed in %.2fs – %d chunks indexed",
            time.perf_counter() - start,
            chunks_indexed,
        )
        return {"message": "File uploaded successfully", "chunks": chunks_indexed}
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=str(e))