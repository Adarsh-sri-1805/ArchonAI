"""
app/services/settings_service.py
--------------------------------
Settings management service for Archon AI.
Persists user configuration (LLM providers, API keys, models, hyperparameters)
to storage/settings.json and dynamically reconfigures runtime services.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.llm_service import build_chat_provider, test_provider_key
from app.services.embedding_service import build_embedding_provider

logger = logging.getLogger("archon.settings")

SETTINGS_FILE = settings.STORAGE_ROOT / "settings.json"


def _mask_key(key: str) -> str:
    """Mask sensitive API key strings for secure frontend display."""
    if not key or len(key) < 8:
        return "****" if key else ""
    return f"{key[:6]}...{key[-4:]}"


class SettingsService:

    def __init__(self, storage_path: Path = SETTINGS_FILE):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._current_config = self._load()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "chat_provider": getattr(settings, "CHAT_PROVIDER", "gemini"),
            "temperature": 0.3,
            "gemini_api_key": getattr(settings, "GEMINI_API_KEY", ""),
            "gemini_model": getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
            "groq_api_key": getattr(settings, "GROQ_API_KEY", ""),
            "groq_model": getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
            "openai_api_key": getattr(settings, "OPENAI_API_KEY", ""),
            "openai_model": getattr(settings, "OPENAI_MODEL", "gpt-4o"),
            "anthropic_api_key": getattr(settings, "ANTHROPIC_API_KEY", ""),
            "anthropic_model": "claude-3-5-sonnet-20241022",
            "embedding_provider": getattr(settings, "EMBEDDING_PROVIDER", "sentence_transformer"),
            "embedding_model": getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            "top_k": getattr(settings, "TOP_K", 5),
            "rerank_enabled": True,
            "chunk_size": getattr(settings, "CHUNK_SIZE", 1000),
            "chunk_overlap": getattr(settings, "CHUNK_OVERLAP", 200),
            "system_prompt_mode": "default",  # "default", "concise", "deep"
        }

    def _load(self) -> Dict[str, Any]:
        defaults = self._default_config()
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                defaults.update(data)
            except Exception as e:
                logger.warning("Failed to load settings file %s: %s", self.storage_path, e)
        return defaults

    def get_settings(self, mask_keys: bool = True) -> Dict[str, Any]:
        cfg = dict(self._current_config)
        if mask_keys:
            cfg["gemini_api_key_masked"] = _mask_key(cfg.get("gemini_api_key", ""))
            cfg["groq_api_key_masked"] = _mask_key(cfg.get("groq_api_key", ""))
            cfg["openai_api_key_masked"] = _mask_key(cfg.get("openai_api_key", ""))
            cfg["anthropic_api_key_masked"] = _mask_key(cfg.get("anthropic_api_key", ""))
            cfg["has_gemini_key"] = bool(cfg.get("gemini_api_key"))
            cfg["has_groq_key"] = bool(cfg.get("groq_api_key"))
            cfg["has_openai_key"] = bool(cfg.get("openai_api_key"))
            cfg["has_anthropic_key"] = bool(cfg.get("anthropic_api_key"))
            # Exclude raw keys from response for safety
            cfg.pop("gemini_api_key", None)
            cfg.pop("groq_api_key", None)
            cfg.pop("openai_api_key", None)
            cfg.pop("anthropic_api_key", None)
        return cfg

    def update_settings(self, updates: Dict[str, Any], app_state: Optional[Any] = None) -> Dict[str, Any]:
        # Preserve existing API key if masked or empty in update payload
        for key in ["gemini_api_key", "groq_api_key", "openai_api_key", "anthropic_api_key"]:
            if key in updates:
                val = updates[key]
                if not val or "..." in val or val.startswith("****"):
                    # keep current key
                    updates[key] = self._current_config.get(key, "")

        self._current_config.update(updates)
        self._persist()

        # Dynamically reconfigure live application state if provided
        if app_state is not None:
            self.apply_to_app_state(app_state)

        return self.get_settings(mask_keys=True)

    def apply_to_app_state(self, app_state: Any) -> None:
        """Re-instantiates active LLM and embedding providers dynamically."""
        cfg = self._current_config
        logger.info("Applying updated settings to runtime services...")

        # Update LLM provider
        app_state.llm_provider = build_chat_provider(
            provider=cfg.get("chat_provider", "gemini"),
            gemini_api_key=cfg.get("gemini_api_key", ""),
            gemini_model=cfg.get("gemini_model", "gemini-2.0-flash"),
            groq_api_key=cfg.get("groq_api_key", ""),
            groq_model=cfg.get("groq_model", "llama-3.3-70b-versatile"),
            openai_api_key=cfg.get("openai_api_key", ""),
            openai_model=cfg.get("openai_model", "gpt-4o"),
            anthropic_api_key=cfg.get("anthropic_api_key", ""),
            anthropic_model=cfg.get("anthropic_model", "claude-3-5-sonnet-20241022"),
            temperature=float(cfg.get("temperature", 0.3)),
        )

        # Update Retrieval Service active configuration
        if hasattr(app_state, "retrieval_service"):
            # Update settings constants
            settings.TOP_K = int(cfg.get("top_k", 5))

    def _persist(self) -> None:
        try:
            self.storage_path.write_text(
                json.dumps(self._current_config, indent=2),
                encoding="utf-8",
            )
            logger.info("Persisted configuration to %s", self.storage_path)
        except Exception as e:
            logger.error("Failed to write settings file: %s", e)

    def test_key(self, provider: str, api_key: str, model: str = "") -> dict:
        # If user passed masked or empty string, use existing stored key
        if not api_key or "..." in api_key or api_key.startswith("****"):
            stored_key_name = f"{provider}_api_key"
            api_key = self._current_config.get(stored_key_name, "")
            if not model:
                model = self._current_config.get(f"{provider}_model", "")

        return test_provider_key(provider=provider, api_key=api_key, model=model)

    def clear_index(self, app_state: Any) -> dict:
        """Clears FAISS index and BM25 store documents."""
        try:
            if hasattr(app_state, "bm25_store") and app_state.bm25_store:
                app_state.bm25_store.documents.clear()
                app_state.bm25_store.corpus_tokens.clear()
                app_state.bm25_store.bm25 = None
            if hasattr(app_state, "vector_store") and app_state.vector_store:
                app_state.vector_store.create_index(
                    kb_id="default",
                    dimension=getattr(settings, "EMBEDDING_DIMENSION", 384),
                )
            return {"success": True, "message": "Knowledge base index cleared successfully."}
        except Exception as e:
            return {"success": False, "message": str(e)}
