from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, model_validator


# ── Knowledge Base (Central DB) ───────────────────────────────────────────────

class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None


class KnowledgeBaseCreate(KnowledgeBaseBase):
    id: str  # Can be a user-provided slug or unique ID


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Document (Partition DB) ───────────────────────────────────────────────────

class DocumentBase(BaseModel):
    filename: str
    content: str
    metadata: Dict[str, Any] = {}


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_metadata(cls, data: Any) -> Any:
        if hasattr(data, "metadata_json"):
            return {
                "id": data.id,
                "filename": data.filename,
                "content": data.content,
                "metadata": data.metadata_json,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


# ── Document Chunk (Partition DB) ─────────────────────────────────────────────

class DocumentChunkBase(BaseModel):
    content: str
    vector_id: Optional[int] = None
    metadata: Dict[str, Any] = {}


class DocumentChunkCreate(DocumentChunkBase):
    document_id: int


class DocumentChunkResponse(DocumentChunkBase):
    id: int
    document_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_metadata(cls, data: Any) -> Any:
        if hasattr(data, "metadata_json"):
            return {
                "id": data.id,
                "document_id": data.document_id,
                "content": data.content,
                "vector_id": data.vector_id,
                "metadata": data.metadata_json,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


# ── Transient Document (Pipeline Ingestion representation) ───────────────────

@dataclass
class Document:
    page_content: str
    metadata: dict = field(default_factory=dict)
