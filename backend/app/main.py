from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.upload import router as upload_router
from app.core.config import settings
from app.services.vector_store import VectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):

    vector_store = VectorStore(
        settings.EMBEDDING_DIMENSION
    )

    vector_store.load()

    app.state.vector_store = vector_store

    yield

from app.services.bm25_store import BM25Store

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.vector_store = VectorStore(384)
    app.state.bm25_store = BM25Store()

    yield
app = FastAPI(
    title="Archon AI",
    lifespan=lifespan,
)

app.include_router(upload_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "Archon AI Backend is Running!"
    }