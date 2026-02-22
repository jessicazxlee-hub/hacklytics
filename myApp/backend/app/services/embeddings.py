from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.vector_store import UserProfileEmbeddingRecord, UserProfileVectorMetadata
from app.services.preference_profile_builder import (
    PREFERENCE_PROFILE_EMBEDDING_VERSION,
    PreferenceProfile,
    build_preference_profile,
)
from app.services.vector_store import VectorStoreAdapter, user_profile_embedding_record_id


USER_PROFILE_EMBEDDING_VERSION = "user_profile_embed_v1"
FAKE_EMBEDDING_MODEL = "fake-deterministic-embedding-v1"


class EmbeddingProvider(Protocol):
    model_name: str

    def embed_text(self, text: str) -> list[float]:
        ...


@dataclass(frozen=True)
class FakeEmbedder:
    """Deterministic fake embedder for pipeline development and tests.

    It hashes the input text and expands the digest into a stable float vector.
    """

    dimension: int = 16
    model_name: str = FAKE_EMBEDDING_MODEL

    def embed_text(self, text: str) -> list[float]:
        if self.dimension <= 0:
            raise ValueError("FakeEmbedder dimension must be > 0")

        seed = text.encode("utf-8")
        floats: list[float] = []
        counter = 0
        while len(floats) < self.dimension:
            digest = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            counter += 1
            for i in range(0, len(digest), 4):
                chunk = digest[i : i + 4]
                if len(chunk) < 4:
                    continue
                value = int.from_bytes(chunk, "big", signed=False)
                # Map into [-1.0, 1.0] deterministically.
                floats.append((value / 0xFFFFFFFF) * 2.0 - 1.0)
                if len(floats) >= self.dimension:
                    break
        return floats


@dataclass(frozen=True)
class UserProfileEmbeddingUpsertResult:
    user_id: UUID
    record_id: str
    embedding_version: str
    embedding_model: str
    preference_profile_version: str
    source_content_hash: str
    vector_dimension: int


def source_content_hash(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _vector_metadata_from_profile(profile: PreferenceProfile) -> UserProfileVectorMetadata:
    return UserProfileVectorMetadata(
        discoverable=profile.metadata.discoverable,
        open_to_meetups=profile.metadata.open_to_meetups,
        neighborhood=profile.metadata.neighborhood,
        geohash=profile.metadata.geohash,
        budget_min=profile.metadata.budget_min,
        budget_max=profile.metadata.budget_max,
        hobbies=profile.features.hobbies,
        diet_tags=profile.features.diet_tags,
        vibe_tags=profile.features.vibe_tags,
    )


def build_user_profile_embedding_record(
    db: Session,
    *,
    user_id: UUID,
    embedder: EmbeddingProvider,
    embedding_version: str = USER_PROFILE_EMBEDDING_VERSION,
) -> UserProfileEmbeddingRecord:
    profile = build_preference_profile(db, user_id)
    text = profile.text_for_embedding
    vector = embedder.embed_text(text)
    now = datetime.now(timezone.utc)

    return UserProfileEmbeddingRecord(
        id=user_profile_embedding_record_id(profile.user_id, embedding_version),
        user_id=str(profile.user_id),
        vector=vector,
        embedding_version=embedding_version,
        embedding_model=embedder.model_name,
        preference_profile_version=profile.embedding_version,
        source_content_hash=source_content_hash(text),
        metadata=_vector_metadata_from_profile(profile),
        created_at=now,
        updated_at=now,
    )


def upsert_user_profile_embedding(
    db: Session,
    *,
    user_id: UUID,
    vector_store: VectorStoreAdapter,
    embedder: EmbeddingProvider,
    embedding_version: str = USER_PROFILE_EMBEDDING_VERSION,
) -> UserProfileEmbeddingUpsertResult:
    record = build_user_profile_embedding_record(
        db,
        user_id=user_id,
        embedder=embedder,
        embedding_version=embedding_version,
    )
    vector_store.upsert_user_profile_embedding(record)
    return UserProfileEmbeddingUpsertResult(
        user_id=user_id,
        record_id=record.id,
        embedding_version=record.embedding_version,
        embedding_model=record.embedding_model,
        preference_profile_version=record.preference_profile_version,
        source_content_hash=record.source_content_hash,
        vector_dimension=len(record.vector),
    )


def upsert_user_profile_embeddings_batch(
    db: Session,
    *,
    user_ids: list[UUID],
    vector_store: VectorStoreAdapter,
    embedder: EmbeddingProvider,
    embedding_version: str = USER_PROFILE_EMBEDDING_VERSION,
) -> list[UserProfileEmbeddingUpsertResult]:
    records: list[UserProfileEmbeddingRecord] = []
    for user_id in user_ids:
        records.append(
            build_user_profile_embedding_record(
                db,
                user_id=user_id,
                embedder=embedder,
                embedding_version=embedding_version,
            )
        )

    if records:
        vector_store.upsert_user_profile_embeddings(records)

    return [
        UserProfileEmbeddingUpsertResult(
            user_id=UUID(record.user_id),
            record_id=record.id,
            embedding_version=record.embedding_version,
            embedding_model=record.embedding_model,
            preference_profile_version=record.preference_profile_version,
            source_content_hash=record.source_content_hash,
            vector_dimension=len(record.vector),
        )
        for record in records
    ]


__all__ = [
    "EmbeddingProvider",
    "FakeEmbedder",
    "FAKE_EMBEDDING_MODEL",
    "PREFERENCE_PROFILE_EMBEDDING_VERSION",
    "USER_PROFILE_EMBEDDING_VERSION",
    "UserProfileEmbeddingUpsertResult",
    "build_user_profile_embedding_record",
    "source_content_hash",
    "upsert_user_profile_embedding",
    "upsert_user_profile_embeddings_batch",
]

