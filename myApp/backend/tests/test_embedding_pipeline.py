from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.models.user import User
from app.schemas.vector_store import UserProfileEmbeddingRecord
from app.services.embeddings import (
    FakeEmbedder,
    USER_PROFILE_EMBEDDING_VERSION,
    build_user_profile_embedding_record,
    upsert_user_profile_embedding,
    upsert_user_profile_embeddings_batch,
)


@dataclass
class FakeVectorStore:
    records: list[UserProfileEmbeddingRecord] = field(default_factory=list)
    batch_calls: int = 0

    def upsert_user_profile_embedding(self, record: UserProfileEmbeddingRecord) -> None:
        self.records.append(record)

    def upsert_user_profile_embeddings(self, records: list[UserProfileEmbeddingRecord]) -> None:
        self.batch_calls += 1
        self.records.extend(records)

    def query_similar_user_profiles(self, query):  # pragma: no cover - not used here
        return []

    def delete_user_profile_embedding(self, *, user_id: str, embedding_version: str) -> bool:  # pragma: no cover
        return False

    def delete_user_profile_embeddings_for_user(self, *, user_id: str) -> int:  # pragma: no cover
        return 0

    def healthcheck(self) -> bool:  # pragma: no cover
        return True


def _create_user(db: Session, *, email: str, neighborhood: str | None = "Midtown") -> UUID:
    user = User(
        id=uuid4(),
        email=email,
        firebase_uid=f"firebase-{uuid4().hex[:8]}",
        display_name=email.split("@")[0],
        neighborhood=neighborhood,
        discoverable=True,
        open_to_meetups=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


def test_fake_embedder_is_deterministic():
    embedder = FakeEmbedder(dimension=8)
    text = "Proximity user preference profile\nhobbies: coffee"
    v1 = embedder.embed_text(text)
    v2 = embedder.embed_text(text)
    assert v1 == v2
    assert len(v1) == 8
    assert any(value != 0.0 for value in v1)


def test_build_user_profile_embedding_record_is_deterministic_for_same_profile(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()
    user_id = _create_user(db, email="embedder-deterministic@example.com")
    embedder = FakeEmbedder(dimension=12)

    record1 = build_user_profile_embedding_record(db, user_id=user_id, embedder=embedder)
    record2 = build_user_profile_embedding_record(db, user_id=user_id, embedder=embedder)

    assert record1.id == record2.id
    assert record1.embedding_version == USER_PROFILE_EMBEDDING_VERSION
    assert record1.embedding_model == embedder.model_name
    assert record1.preference_profile_version == record2.preference_profile_version
    assert record1.source_content_hash == record2.source_content_hash
    assert record1.vector == record2.vector
    assert record1.metadata.open_to_meetups is True
    assert len(record1.vector) == 12
    db.close()


def test_upsert_user_profile_embedding_calls_vector_store_with_record(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()
    user_id = _create_user(db, email="embedder-upsert@example.com")
    vector_store = FakeVectorStore()
    embedder = FakeEmbedder(dimension=10)

    result = upsert_user_profile_embedding(
        db,
        user_id=user_id,
        vector_store=vector_store,
        embedder=embedder,
    )

    assert result.user_id == user_id
    assert result.embedding_version == USER_PROFILE_EMBEDDING_VERSION
    assert result.embedding_model == embedder.model_name
    assert result.vector_dimension == 10
    assert len(vector_store.records) == 1
    stored = vector_store.records[0]
    assert stored.user_id == str(user_id)
    assert stored.source_content_hash == result.source_content_hash
    db.close()


def test_upsert_user_profile_embeddings_batch_uses_batch_call(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()
    user1 = _create_user(db, email="batch1@example.com")
    user2 = _create_user(db, email="batch2@example.com", neighborhood="Downtown")
    vector_store = FakeVectorStore()
    embedder = FakeEmbedder(dimension=6)

    results = upsert_user_profile_embeddings_batch(
        db,
        user_ids=[user1, user2],
        vector_store=vector_store,
        embedder=embedder,
    )

    assert len(results) == 2
    assert vector_store.batch_calls == 1
    assert len(vector_store.records) == 2
    assert {UUID(record.user_id) for record in vector_store.records} == {user1, user2}
    db.close()

