from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.models.user import User
from app.schemas.vector_store import UserProfileVectorQuery
from app.services.actian_vector_store import ActianVectorStoreAdapter, ActianVectorStoreConfig


class FakeCortexClient:
    def __init__(self) -> None:
        self.points: dict[int, dict] = {}
        self.deleted_ids: list[int] = []
        self.flushed = False

    def list_collections(self):
        return ["user_profiles_embed_v1"]

    def upsert(self, *, id: int, vector: list[float], payload: dict | None = None) -> None:
        self.points[id] = {"id": id, "vector": vector, "payload": payload}

    def batch_upsert(self, points=None, **kwargs) -> None:
        values = points if points is not None else kwargs["points"]
        for point in values:
            self.points[int(point["id"])] = point

    def search(self, **kwargs):
        with_payload = kwargs.get("with_payload", True)
        self.last_search_kwargs = kwargs
        results = []
        for point_id, point in self.points.items():
            payload = point.get("payload") if with_payload else None
            results.append({"id": point_id, "score": 0.9, "payload": payload})
        return results

    def delete(self, *, id: int) -> None:
        self.deleted_ids.append(id)
        self.points.pop(id, None)

    def flush(self) -> None:
        self.flushed = True


class FakeCortexClientNoFilter(FakeCortexClient):
    def search(self, **kwargs):
        if "filter" in kwargs:
            raise RuntimeError("filtered search not supported")
        return super().search(**kwargs)


def _make_adapter(db: Session, fake_client: FakeCortexClient) -> ActianVectorStoreAdapter:
    return ActianVectorStoreAdapter(
        db=db,
        config=ActianVectorStoreConfig(address="localhost:50051", collection_name="user_profiles_embed_v1"),
        client=fake_client,
    )


def _record(user_id: str, embedding_version: str = "user_profile_embed_v1"):
    return ActianVectorStoreAdapter.build_record(
        user_id=user_id,
        vector=[0.1, 0.2, 0.3],
        embedding_version=embedding_version,
        embedding_model="gemini-text-embedding-004",
        preference_profile_version="preference_profile_v1",
        source_content_hash=f"sha256:{user_id}",
        metadata={
            "discoverable": True,
            "open_to_meetups": True,
            "neighborhood": "Midtown",
            "geohash": None,
            "budget_min": 10,
            "budget_max": 50,
            "hobbies": ["coffee"],
            "diet_tags": [],
            "vibe_tags": [],
        },
    )


def _create_user(db: Session, user_id: str, email: str) -> None:
    db.add(
        User(
            id=UUID(user_id),
            email=email,
            firebase_uid=f"firebase-{user_id[:8]}",
        )
    )
    db.commit()


def test_actian_adapter_upsert_query_delete_with_mapping(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()
    fake = FakeCortexClient()
    adapter = _make_adapter(db, fake)

    user1 = str(uuid4())
    user2 = str(uuid4())
    _create_user(db, user1, "actian-test-1@example.com")
    _create_user(db, user2, "actian-test-2@example.com")
    r1 = _record(user1)
    r2 = _record(user2)

    adapter.upsert_user_profile_embedding(r1)
    adapter.upsert_user_profile_embedding(r2)
    adapter.flush()

    assert fake.flushed is True
    assert len(fake.points) == 2

    matches = adapter.query_similar_user_profiles(
        UserProfileVectorQuery(
            query_vector=[0.1, 0.2, 0.3],
            top_k=10,
            embedding_version="user_profile_embed_v1",
            exclude_user_ids=[user2],
        )
    )
    assert any(match.user_id == user1 for match in matches)
    assert all(match.user_id != user2 for match in matches)

    deleted = adapter.delete_user_profile_embedding(
        user_id=user1, embedding_version="user_profile_embed_v1"
    )
    assert deleted is True
    assert len(fake.points) == 1

    deleted_count = adapter.delete_user_profile_embeddings_for_user(user_id=user2)
    assert deleted_count == 1
    assert len(fake.points) == 0
    db.close()


def test_actian_adapter_healthcheck_uses_client(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()
    fake = FakeCortexClient()
    adapter = _make_adapter(db, fake)

    assert adapter.healthcheck() is True
    db.close()


def test_actian_adapter_batch_upsert_assigns_unique_point_ids(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()
    fake = FakeCortexClient()
    adapter = _make_adapter(db, fake)

    user_ids = [str(uuid4()) for _ in range(3)]
    for idx, user_id in enumerate(user_ids):
        _create_user(db, user_id, f"actian-batch-{idx}@example.com")

    records = [_record(user_id) for user_id in user_ids]
    adapter.upsert_user_profile_embeddings(records)

    assert len(fake.points) == 3
    assert len(set(fake.points.keys())) == 3
    db.close()


def test_actian_config_from_settings():
    settings = Settings(
        vectorai_enabled=True,
        vectorai_address="10.0.0.5:50051",
        vectorai_api_key="abc123",
        vectorai_collection_name="user_profiles_embed_v2",
        vectorai_metric="COSINE",
        vectorai_dimension=768,
        vectorai_supports_metadata_filtering=True,
        vectorai_batch_upsert_size=77,
        vectorai_request_timeout_seconds=5.0,
    )
    cfg = ActianVectorStoreConfig.from_settings(settings)
    assert cfg.address == "10.0.0.5:50051"
    assert cfg.api_key == "abc123"
    assert cfg.collection_name == "user_profiles_embed_v2"
    assert cfg.dimension == 768
    assert cfg.supports_metadata_filtering is True
    assert cfg.batch_upsert_size == 77


def test_probe_metadata_filtering_support_true_with_fake_client(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()
    fake = FakeCortexClient()
    adapter = ActianVectorStoreAdapter(
        db=db,
        config=ActianVectorStoreConfig(
            address="localhost:50051",
            collection_name="user_profiles_embed_v1",
            dimension=4,
        ),
        client=fake,
    )
    assert adapter.probe_metadata_filtering_support() is True
    assert "filter" in fake.last_search_kwargs
    db.close()


def test_probe_metadata_filtering_support_false_when_search_rejects_filter(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()
    fake = FakeCortexClientNoFilter()
    adapter = ActianVectorStoreAdapter(
        db=db,
        config=ActianVectorStoreConfig(
            address="localhost:50051",
            collection_name="user_profiles_embed_v1",
            dimension=4,
        ),
        client=fake,
    )
    assert adapter.probe_metadata_filtering_support() is False
    db.close()
