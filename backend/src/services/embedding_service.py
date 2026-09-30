from typing import List, Optional

from src.core.config import settings
from src.infrastructure.llm.embedding_providers import (
    EmbeddingProvider,
    build_embedding_provider,
)


class EmbeddingService:
    """
    Application service that wraps an EmbeddingProvider adapter.
    Allows injecting custom providers (e.g. mock/test adapters) or
    defaults to building the provider using global settings.
    """

    def __init__(self, provider: Optional[EmbeddingProvider] = None):
        if provider is None:
            # Fall back to global configuration settings
            provider = build_embedding_provider(
                provider=settings.EMBEDDING_PROVIDER,
                model=settings.EMBEDDING_MODEL,
                api_key=getattr(settings, "GEMINI_API_KEY", "")
            )
        self._provider = provider

    @property
    def dimension(self) -> int:
        """Returns the dimension of the embedding vector."""
        return self._provider.dimension

    def embed_query(self, text: str) -> List[float]:
        """Embeds a single query string."""
        if not text:
            return []
        return self._provider.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a batch of document strings."""
        if not texts:
            return []
        return self._provider.embed_documents(texts)
