"""
app/services/llm_service.py
-----------------------------
ChatCompletionProvider interface + Gemini, Groq, OpenAI, and Fallback adapters.

ChatService depends ONLY on ChatCompletionProvider ABC.
To switch between providers: set CHAT_PROVIDER=fallback, gemini, groq, or openai in .env.
No retrieval or prompt code changes are needed.
"""
from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("archon.llm")


# ── Abstract interface ────────────────────────────────────────────────────────

class ChatCompletionProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str, max_retries: int = 3, temperature: float = 0.3) -> str:
        """Generate a complete text response for the given prompt."""


# ── Gemini adapter ────────────────────────────────────────────────────────────

class GeminiChatProvider(ChatCompletionProvider):
    """
    Wraps the google-genai client.
    Client is created lazily on first call so FastAPI startup stays instant.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", temperature: float = 0.3):
        self._api_key = api_key
        self._model = model
        self.temperature = temperature
        self._client = None  # lazy

    @property
    def _lazy_client(self):
        if self._client is None:
            try:
                from google import genai  # type: ignore
            except ImportError:
                raise RuntimeError(
                    "google-genai not installed. Run: pip install google-genai"
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def generate(self, prompt: str, max_retries: int = 3, temperature: float | None = None) -> str:
        temp = temperature if temperature is not None else self.temperature
        delay = 0.2
        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Gemini request (attempt %d/%d)", attempt, max_retries)
                t0 = time.perf_counter()
                
                # Check config parameter style for google-genai
                config = {"temperature": temp} if hasattr(self._lazy_client, "models") else None
                try:
                    response = self._lazy_client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=config,
                    )
                except TypeError:
                    response = self._lazy_client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                    )
                logger.info("Gemini responded in %.2fs", time.perf_counter() - t0)
                return response.text or ""
            except Exception as e:
                logger.warning("Gemini attempt %d failed: %s", attempt, e)
                if attempt == max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
        return ""


# ── Groq adapter ───────────────────────────────────────────────────────────────

class GroqChatProvider(ChatCompletionProvider):
    """
    Wraps the groq client (or OpenAI client using Groq base_url as fallback).
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", temperature: float = 0.3):
        self._api_key = api_key
        self._model = model
        self.temperature = temperature
        self._client = None  # lazy

    @property
    def _lazy_client(self):
        if self._client is None:
            try:
                from groq import Groq  # type: ignore
                self._client = Groq(api_key=self._api_key)
            except ImportError:
                try:
                    from openai import OpenAI  # type: ignore
                    self._client = OpenAI(
                        api_key=self._api_key,
                        base_url="https://api.groq.com/openai/v1",
                    )
                except ImportError:
                    raise RuntimeError(
                        "Neither 'groq' nor 'openai' package is installed. Run: pip install groq"
                    )
        return self._client

    def generate(self, prompt: str, max_retries: int = 3, temperature: float | None = None) -> str:
        temp = temperature if temperature is not None else self.temperature
        delay = 0.2
        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Groq request (attempt %d/%d)", attempt, max_retries)
                t0 = time.perf_counter()
                response = self._lazy_client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temp,
                )
                logger.info("Groq responded in %.2fs", time.perf_counter() - t0)
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.warning("Groq attempt %d failed: %s", attempt, e)
                if attempt == max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
        return ""


# ── OpenAI adapter ────────────────────────────────────────────────────────────

class OpenAIChatProvider(ChatCompletionProvider):

    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.3):
        self._api_key = api_key
        self._model = model
        self.temperature = temperature
        self._client = None  # lazy

    @property
    def _lazy_client(self):
        if self._client is None:
            try:
                from openai import OpenAI  # type: ignore
            except ImportError:
                raise RuntimeError(
                    "openai not installed. Run: pip install openai"
                )
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def generate(self, prompt: str, max_retries: int = 3, temperature: float | None = None) -> str:
        temp = temperature if temperature is not None else self.temperature
        response = self._lazy_client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
        )
        return response.choices[0].message.content or ""


# ── Anthropic adapter ─────────────────────────────────────────────────────────

class AnthropicChatProvider(ChatCompletionProvider):

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", temperature: float = 0.3):
        self._api_key = api_key
        self._model = model
        self.temperature = temperature
        self._client = None

    @property
    def _lazy_client(self):
        if self._client is None:
            try:
                import anthropic  # type: ignore
                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                raise RuntimeError("anthropic not installed. Run: pip install anthropic")
        return self._client

    def generate(self, prompt: str, max_retries: int = 3, temperature: float | None = None) -> str:
        temp = temperature if temperature is not None else self.temperature
        response = self._lazy_client.messages.create(
            model=self._model,
            max_tokens=4096,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""


# ── Multimodal Fallback adapter ────────────────────────────────────────────────

class FallbackChatProvider(ChatCompletionProvider):
    """
    Tries a primary provider (e.g. Gemini).
    If the primary provider fails after max_retries, seamlessly switches to fallback.
    """

    def __init__(
        self,
        primary: ChatCompletionProvider,
        fallback: ChatCompletionProvider,
    ):
        self.primary = primary
        self.fallback = fallback

    def generate(self, prompt: str, max_retries: int = 3, temperature: float | None = None) -> str:
        try:
            if temperature is not None:
                try:
                    return self.primary.generate(prompt, max_retries=max_retries, temperature=temperature)
                except TypeError:
                    return self.primary.generate(prompt, max_retries=max_retries)
            return self.primary.generate(prompt, max_retries=max_retries)
        except Exception as e:
            logger.warning(
                "Primary provider failed (%s). Switching to fallback provider: %s",
                e, type(self.fallback).__name__,
            )
            if temperature is not None:
                try:
                    return self.fallback.generate(prompt, max_retries=max_retries, temperature=temperature)
                except TypeError:
                    return self.fallback.generate(prompt, max_retries=max_retries)
            return self.fallback.generate(prompt, max_retries=max_retries)


# ── Factory ───────────────────────────────────────────────────────────────────

def build_chat_provider(
    provider: str,
    gemini_api_key: str = "",
    gemini_model: str = "gemini-2.0-flash",
    groq_api_key: str = "",
    groq_model: str = "llama-3.3-70b-versatile",
    openai_api_key: str = "",
    openai_model: str = "gpt-4o",
    anthropic_api_key: str = "",
    anthropic_model: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0.3,
) -> ChatCompletionProvider:
    gemini = GeminiChatProvider(api_key=gemini_api_key, model=gemini_model, temperature=temperature)
    groq = GroqChatProvider(api_key=groq_api_key, model=groq_model, temperature=temperature)

    if provider == "groq":
        return groq
    if provider == "openai":
        return OpenAIChatProvider(api_key=openai_api_key, model=openai_model, temperature=temperature)
    if provider == "gemini":
        return gemini
    if provider == "anthropic":
        return AnthropicChatProvider(api_key=anthropic_api_key, model=anthropic_model, temperature=temperature)

    # Default fallback
    return FallbackChatProvider(primary=gemini, fallback=groq)


def test_provider_key(provider: str, api_key: str, model: str = "") -> dict:
    """
    Validates an API key with a ping test against the chosen provider.
    Returns {"success": bool, "message": str}.
    """
    if not api_key.strip():
        return {"success": False, "message": "API Key is empty"}

    try:
        if provider == "gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            test_model = model or "gemini-2.0-flash"
            resp = client.models.generate_content(
                model=test_model,
                contents="Say 'OK'",
            )
            return {"success": True, "message": f"Connected to Gemini ({test_model}) successfully!"}

        elif provider == "groq":
            try:
                from groq import Groq
                client = Groq(api_key=api_key)
            except ImportError:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            test_model = model or "llama-3.3-70b-versatile"
            resp = client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
            return {"success": True, "message": f"Connected to Groq ({test_model}) successfully!"}

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            test_model = model or "gpt-4o-mini"
            resp = client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
            return {"success": True, "message": f"Connected to OpenAI ({test_model}) successfully!"}

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            test_model = model or "claude-3-5-sonnet-20241022"
            resp = client.messages.create(
                model=test_model,
                max_tokens=5,
                messages=[{"role": "user", "content": "Say OK"}],
            )
            return {"success": True, "message": f"Connected to Anthropic ({test_model}) successfully!"}

        return {"success": False, "message": f"Unknown provider: {provider}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


