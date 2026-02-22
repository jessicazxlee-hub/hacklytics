from __future__ import annotations

from app.core.config import settings


def _admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": settings.admin_api_key}


def _register_user(client, *, email: str, firebase_uid: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "firebase_uid": firebase_uid,
            "neighborhood": "Downtown",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_admin_embedding_upsert_disabled_returns_503(client, monkeypatch):
    user = _register_user(client, email="embed-disabled@example.com", firebase_uid="firebase-embed-disabled")
    monkeypatch.setattr(settings, "vectorai_enabled", False)

    response = client.post(
        f"/api/v1/admin/embeddings/users/{user['id']}/upsert",
        headers=_admin_headers(),
        json={},
    )
    assert response.status_code == 503, response.text
    assert response.json()["detail"] == "VECTORAI_ENABLED is false"


def test_admin_embedding_upsert_by_user_id_happy_path(client, monkeypatch):
    from app.api.v1.routes import admin_embeddings as route_mod
    from app.crud.vector_index import upsert_user_vector_point_id

    class FakeAdapter:
        _next_point_id = 2000

        def __init__(self, *, db, config):
            self._db = db
            self._config = config
            self.provider = "actian"
            self.collection_name = config.collection_name

        def ensure_collection(self) -> None:
            return None

        def flush(self) -> None:
            return None

        def upsert_user_profile_embedding(self, record):
            FakeAdapter._next_point_id += 1
            upsert_user_vector_point_id(
                self._db,
                user_id=route_mod.UUID(record.user_id),
                provider=self.provider,
                collection_name=self.collection_name,
                embedding_version=record.embedding_version,
                point_id=FakeAdapter._next_point_id,
            )

    monkeypatch.setattr(settings, "vectorai_enabled", True)
    monkeypatch.setattr(settings, "vectorai_address", "127.0.0.1:50051")
    monkeypatch.setattr(settings, "vectorai_collection_name", "user_profiles_embed_v1_test")
    monkeypatch.setattr(settings, "vectorai_metric", "COSINE")
    monkeypatch.setattr(settings, "vectorai_dimension", 4)
    monkeypatch.setattr(route_mod, "ActianVectorStoreAdapter", FakeAdapter)

    user = _register_user(client, email="embed-userid@example.com", firebase_uid="firebase-embed-userid")
    response = client.post(
        f"/api/v1/admin/embeddings/users/{user['id']}/upsert",
        headers=_admin_headers(),
        json={},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user_id"] == user["id"]
    assert body["provider"] == "actian"
    assert body["collection_name"] == "user_profiles_embed_v1_test"
    assert isinstance(body["point_id"], int)
    assert body["upsert_result"]["embedding_model"] == "fake-deterministic-embedding-v1"
    assert body["upsert_result"]["vector_dimension"] == 4


def test_admin_embedding_upsert_by_email_convenience_path(client, monkeypatch):
    from app.api.v1.routes import admin_embeddings as route_mod
    from app.crud.vector_index import upsert_user_vector_point_id

    class FakeAdapter:
        _next_point_id = 3000

        def __init__(self, *, db, config):
            self._db = db
            self.provider = "actian"
            self.collection_name = config.collection_name

        def ensure_collection(self) -> None:
            return None

        def flush(self) -> None:
            return None

        def upsert_user_profile_embedding(self, record):
            FakeAdapter._next_point_id += 1
            upsert_user_vector_point_id(
                self._db,
                user_id=route_mod.UUID(record.user_id),
                provider=self.provider,
                collection_name=self.collection_name,
                embedding_version=record.embedding_version,
                point_id=FakeAdapter._next_point_id,
            )

    monkeypatch.setattr(settings, "vectorai_enabled", True)
    monkeypatch.setattr(settings, "vectorai_address", "127.0.0.1:50051")
    monkeypatch.setattr(settings, "vectorai_collection_name", "user_profiles_embed_v1_test")
    monkeypatch.setattr(settings, "vectorai_metric", "COSINE")
    monkeypatch.setattr(settings, "vectorai_dimension", 4)
    monkeypatch.setattr(route_mod, "ActianVectorStoreAdapter", FakeAdapter)

    _register_user(client, email="embed-email@example.com", firebase_uid="firebase-embed-email")
    response = client.post(
        "/api/v1/admin/embeddings/users/by-email/upsert",
        headers=_admin_headers(),
        json={"email": "embed-email@example.com", "fake_dimension_override": 8},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email"] == "embed-email@example.com"
    assert body["upsert_result"]["vector_dimension"] == 8


def test_admin_embedding_upsert_batch_by_explicit_emails(client, monkeypatch):
    from app.api.v1.routes import admin_embeddings as route_mod
    from app.crud.vector_index import upsert_user_vector_point_id

    class FakeAdapter:
        _next_point_id = 4000

        def __init__(self, *, db, config):
            self._db = db
            self.provider = "actian"
            self.collection_name = config.collection_name

        def ensure_collection(self) -> None:
            return None

        def flush(self) -> None:
            return None

        def upsert_user_profile_embedding(self, record):
            FakeAdapter._next_point_id += 1
            upsert_user_vector_point_id(
                self._db,
                user_id=route_mod.UUID(record.user_id),
                provider=self.provider,
                collection_name=self.collection_name,
                embedding_version=record.embedding_version,
                point_id=FakeAdapter._next_point_id,
            )

        def upsert_user_profile_embeddings(self, records):
            for record in records:
                self.upsert_user_profile_embedding(record)

    monkeypatch.setattr(settings, "vectorai_enabled", True)
    monkeypatch.setattr(settings, "vectorai_address", "127.0.0.1:50051")
    monkeypatch.setattr(settings, "vectorai_collection_name", "user_profiles_embed_v1_test")
    monkeypatch.setattr(settings, "vectorai_metric", "COSINE")
    monkeypatch.setattr(settings, "vectorai_dimension", 4)
    monkeypatch.setattr(route_mod, "ActianVectorStoreAdapter", FakeAdapter)

    _register_user(client, email="batch-on-a@example.com", firebase_uid="firebase-batch-on-a")
    _register_user(client, email="batch-on-b@example.com", firebase_uid="firebase-batch-on-b")
    _register_user(client, email="batch-off@example.com", firebase_uid="firebase-batch-off")

    response = client.post(
        "/api/v1/admin/embeddings/upsert-batch",
        headers=_admin_headers(),
        json={
            "emails": ["batch-on-a@example.com", "batch-on-b@example.com"],
            "fake_dimension_override": 4,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["selected_count"] == 2
    assert body["upserted_count"] == 2
    assert body["embedding_version"] == "user_profile_embed_v1"
    assert len(body["results"]) == 2
    assert {row["email"] for row in body["results"]} == {"batch-on-a@example.com", "batch-on-b@example.com"}
    assert all(isinstance(row["point_id"], int) for row in body["results"])
