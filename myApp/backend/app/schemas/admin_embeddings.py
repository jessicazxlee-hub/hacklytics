from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AdminEmbeddingUpsertRequest(BaseModel):
    ensure_collection: bool = True
    flush: bool = True
    fake_dimension_override: int | None = Field(default=None, gt=0)
    embedding_version: str | None = None


class AdminEmbeddingUpsertByEmailRequest(AdminEmbeddingUpsertRequest):
    email: EmailStr


class AdminEmbeddingUpsertBatchRequest(AdminEmbeddingUpsertRequest):
    user_ids: list[UUID] = Field(default_factory=list)
    emails: list[EmailStr] = Field(default_factory=list)
    mode: Literal["in_person", "chat_only"] | None = None
    only_discoverable: bool = True
    limit: int | None = Field(default=None, ge=1, le=1000)


class AdminEmbeddingUpsertResultRead(BaseModel):
    user_id: UUID
    record_id: str
    embedding_version: str
    embedding_model: str
    preference_profile_version: str
    source_content_hash: str
    vector_dimension: int


class AdminEmbeddingUpsertResponse(BaseModel):
    user_id: UUID
    email: str
    provider: str
    collection_name: str
    point_id: int | None = None
    upsert_result: AdminEmbeddingUpsertResultRead
    warnings: list[str] = Field(default_factory=list)


class AdminEmbeddingUpsertBatchResponse(BaseModel):
    selected_count: int
    upserted_count: int
    provider: str
    collection_name: str
    embedding_version: str
    results: list[AdminEmbeddingUpsertResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
