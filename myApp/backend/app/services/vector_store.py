from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.vector_store import (
    UserProfileEmbeddingRecord,
    UserProfileVectorMatch,
    UserProfileVectorQuery,
)


USER_PROFILE_ENTITY_TYPE = "user_profile"


def user_profile_embedding_record_id(user_id: str | UUID, embedding_version: str) -> str:
    return f"{USER_PROFILE_ENTITY_TYPE}:{user_id}:{embedding_version}"


class VectorStoreAdapter(Protocol):
    """Generic vector store adapter contract for profile embeddings."""

    def upsert_user_profile_embedding(self, record: UserProfileEmbeddingRecord) -> None:
        ...

    def upsert_user_profile_embeddings(
        self, records: list[UserProfileEmbeddingRecord]
    ) -> None:
        ...

    def query_similar_user_profiles(
        self, query: UserProfileVectorQuery
    ) -> list[UserProfileVectorMatch]:
        ...

    def delete_user_profile_embedding(
        self, *, user_id: str, embedding_version: str
    ) -> bool:
        ...

    def delete_user_profile_embeddings_for_user(self, *, user_id: str) -> int:
        ...

    def healthcheck(self) -> bool:
        ...


class NotImplementedVectorStoreAdapter:
    """Placeholder implementation until a provider-specific adapter is wired."""

    def upsert_user_profile_embedding(self, record: UserProfileEmbeddingRecord) -> None:
        raise NotImplementedError("Vector store adapter not configured")

    def upsert_user_profile_embeddings(
        self, records: list[UserProfileEmbeddingRecord]
    ) -> None:
        raise NotImplementedError("Vector store adapter not configured")

    def query_similar_user_profiles(
        self, query: UserProfileVectorQuery
    ) -> list[UserProfileVectorMatch]:
        raise NotImplementedError("Vector store adapter not configured")

    def delete_user_profile_embedding(
        self, *, user_id: str, embedding_version: str
    ) -> bool:
        raise NotImplementedError("Vector store adapter not configured")

    def delete_user_profile_embeddings_for_user(self, *, user_id: str) -> int:
        raise NotImplementedError("Vector store adapter not configured")

    def healthcheck(self) -> bool:
        raise NotImplementedError("Vector store adapter not configured")

