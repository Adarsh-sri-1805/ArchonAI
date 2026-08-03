from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.services.chunker import chunk_documents
from app.services.embedder import embed_documents
from app.services.parser import parse_document

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    try:
        file_path = UPLOAD_DIR / file.filename

        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Parse
        documents = parse_document(file_path)

        # Chunk
        documents = chunk_documents(documents)

        # Embed
        embeddings = embed_documents(documents)

        # Store
        request.app.state.vector_store.add(
            embeddings=embeddings,
            documents=documents,
        )

        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "documents_indexed": len(documents),
            "total_embeddings": len(embeddings),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )