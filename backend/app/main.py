"""
app/main.py
-----------
FastAPI application entry point.
- Uses the new service classes (EmbeddingService, VectorStoreService, BM25Store, GitService, IndexingService, RetrievalService, LLMService).
- All heavy initialization is performed in the async lifespan context manager.
- Routers are mounted after the state is ready.
"""
from __future__ import annotations

import threading
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import upload, chat, github, search, stats, settings as settings_api
from app.core.config import settings

# Service implementations
from app.services.embedding_service import build_embedding_provider, EmbeddingProvider
from app.services.vector_store_service import FAISSVectorStoreProvider, VectorStoreProvider
from app.services.bm25_store import BM25Store
from app.services.git_service import GitService
from app.services.indexing_service import IndexingService
from app.services.retrieval_service import RetrievalService
from app.services.llm_service import build_chat_provider, ChatCompletionProvider
from app.services.reranker import warmup_reranker
from app.services.settings_service import SettingsService

logger = logging.getLogger("archon.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared services and attach them to ``app.state``.

    The objects are lightweight and reusable across requests.
    They are created once when the application starts.
    """
    # 0️⃣ Settings Service (reads user customizations & API keys from storage)
    settings_service = SettingsService()
    saved_cfg = settings_service._current_config

    # 1️⃣ Embedding provider (config‑driven)
    emb_provider_name = saved_cfg.get("embedding_provider", settings.EMBEDDING_PROVIDER)
    emb_model_name = saved_cfg.get("embedding_model", settings.EMBEDDING_MODEL)
    gemini_key = saved_cfg.get("gemini_api_key") or getattr(settings, "GEMINI_API_KEY", "")

    embedding: EmbeddingProvider = build_embedding_provider(
        provider=emb_provider_name,
        model=emb_model_name,
        api_key=gemini_key,
    )

    # 2️⃣ Vector store – one FAISS index per knowledge‑base
    vector_store: VectorStoreProvider = FAISSVectorStoreProvider(
        storage_root=str(settings.STORAGE_ROOT),
        dimension=settings.EMBEDDING_DIMENSION,
    )
    vector_store.create_index(kb_id="default", dimension=settings.EMBEDDING_DIMENSION)

    # 3️⃣ BM25 lexical store
    bm25 = BM25Store()

    # 4️⃣ Git service – handles clone/pull of repositories
    git_service = GitService()

    # 5️⃣ Indexing orchestrator – wires up the above components
    indexing = IndexingService(
        embedding_provider=embedding,
        vector_store=vector_store,
        bm25_store=bm25,
    )

    # 6️⃣ Retrieval orchestrator – hybrid search + RRF + reranker
    retrieval = RetrievalService(
        embedding_provider=embedding,
        vector_store=vector_store,
        bm25_store=bm25,
    )

    # 7️⃣ LLM provider – Gemini, Groq, OpenAI, Anthropic
    llm: ChatCompletionProvider = build_chat_provider(
        provider=saved_cfg.get("chat_provider", settings.CHAT_PROVIDER),
        gemini_api_key=saved_cfg.get("gemini_api_key") or getattr(settings, "GEMINI_API_KEY", ""),
        gemini_model=saved_cfg.get("gemini_model") or getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
        groq_api_key=saved_cfg.get("groq_api_key") or getattr(settings, "GROQ_API_KEY", ""),
        groq_model=saved_cfg.get("groq_model") or getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
        openai_api_key=saved_cfg.get("openai_api_key") or getattr(settings, "OPENAI_API_KEY", ""),
        openai_model=saved_cfg.get("openai_model") or getattr(settings, "OPENAI_MODEL", "gpt-4o"),
        anthropic_api_key=saved_cfg.get("anthropic_api_key", ""),
        anthropic_model=saved_cfg.get("anthropic_model", "claude-3-5-sonnet-20241022"),
        temperature=float(saved_cfg.get("temperature", 0.3)),
    )

    # Expose everything via ``app.state`` for the routers to reuse
    app.state.upload_dir = settings.UPLOAD_DIR
    app.state.embedding = embedding
    app.state.vector_store = vector_store
    app.state.bm25_store = bm25
    app.state.git_service = git_service
    app.state.indexing_service = indexing
    app.state.retrieval_service = retrieval
    app.state.llm_provider = llm
    app.state.settings_service = settings_service

    # 🚀 Background Model Pre-Warming:
    # Pre-loads SentenceTransformer & CrossEncoder weights so query #1 has 0s cold-start!
    def background_warmup():
        try:
            logger.info("Starting background model pre-warming...")
            embedding.warmup()
            warmup_reranker()
            logger.info("All neural models pre-warmed and ready in RAM.")
        except Exception as e:
            logger.warning("Background warmup notice: %s", e)

    threading.Thread(target=background_warmup, daemon=True).start()

    yield


# ---------------------------------------------------------------------------
# Application construction
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Archon AI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(github.router)
app.include_router(search.router)
app.include_router(stats.router)
app.include_router(settings_api.router)


@app.get("/")
def root():
    return {"message": "Archon AI Backend is Running!"}