"""
app/api/settings.py
-------------------
REST API endpoints for viewing and updating system settings, API keys,
testing LLM connectivity, and managing the knowledge base index.
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException

from app.core.logger import logger

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdateRequest(BaseModel):
    chat_provider: Optional[str] = None
    temperature: Optional[float] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    groq_api_key: Optional[str] = None
    groq_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    anthropic_model: Optional[str] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    top_k: Optional[int] = None
    rerank_enabled: Optional[bool] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    system_prompt_mode: Optional[str] = None


class TestKeyRequest(BaseModel):
    provider: str
    api_key: Optional[str] = ""
    model: Optional[str] = ""


@router.get("")
def get_settings(request: Request):
    """Retrieve current settings with sensitive API keys safely masked."""
    settings_service = getattr(request.app.state, "settings_service", None)
    if not settings_service:
        raise HTTPException(status_code=500, detail="Settings service not initialized")
    return settings_service.get_settings(mask_keys=True)


@router.post("")
def update_settings(request: Request, body: SettingsUpdateRequest):
    """Update settings and dynamically reload live LLM and retrieval services."""
    settings_service = getattr(request.app.state, "settings_service", None)
    if not settings_service:
        raise HTTPException(status_code=500, detail="Settings service not initialized")

    # Filter out None fields
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = settings_service.update_settings(updates, app_state=request.app.state)
    logger.info("Updated settings: %s", list(updates.keys()))
    return updated


@router.post("/test-key")
def test_key(request: Request, body: TestKeyRequest):
    """Test API key connection to the chosen provider."""
    settings_service = getattr(request.app.state, "settings_service", None)
    if not settings_service:
        raise HTTPException(status_code=500, detail="Settings service not initialized")

    result = settings_service.test_key(
        provider=body.provider,
        api_key=body.api_key or "",
        model=body.model or "",
    )
    return result


@router.post("/clear-index")
def clear_index(request: Request):
    """Clear all indexed documents and reset the vector store."""
    settings_service = getattr(request.app.state, "settings_service", None)
    if not settings_service:
        raise HTTPException(status_code=500, detail="Settings service not initialized")

    return settings_service.clear_index(app_state=request.app.state)
