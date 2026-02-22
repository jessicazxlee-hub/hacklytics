from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserProfileVectorMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    discoverable: bool
    open_to_meetups: bool
    neighborhood: str | None = None
    geohash: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    hobbies: list[str] = Field(default_factory=list)
    diet_tags: list[str] = Field(default_factory=list)
    vibe_tags: list[str] = Field(default_factory=list)


class UserProfileEmbeddingRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    entity_type: Literal["user_profile"] = "user_profile"
    user_id: str
    vector: list[float]
    embedding_version: str
    embedding_model: str
    preference_profile_version: str
    source_content_hash: str
    metadata: UserProfileVectorMetadata
    created_at: datetime
    updated_at: datetime


class UserProfileVectorQueryFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    discoverable: bool | None = None
    open_to_meetups: bool | None = None
    neighborhood: str | None = None
    geohash: str | None = None
    budget_min_gte: int | None = None
    budget_max_lte: int | None = None
    hobbies_any: list[str] = Field(default_factory=list)
    diet_tags_any: list[str] = Field(default_factory=list)
    vibe_tags_any: list[str] = Field(default_factory=list)


class UserProfileVectorQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_vector: list[float]
    top_k: int = Field(default=10, gt=0)
    embedding_version: str
    filters: UserProfileVectorQueryFilters = Field(
        default_factory=UserProfileVectorQueryFilters
    )
    exclude_user_ids: list[str] = Field(default_factory=list)
    include_metadata: bool = True


class UserProfileVectorMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    user_id: str
    score: float
    metadata: UserProfileVectorMetadata | None = None

