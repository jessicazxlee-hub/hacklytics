from __future__ import annotations

from app.core.config import settings


def _admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": settings.admin_api_key}


def test_vector_diagnostics_disabled_returns_structured_response(client, monkeypatch):
    monkeypatch.setattr(settings, "vectorai_enabled", False)

    response = client.post("/api/v1/admin/vector/diagnostics", headers=_admin_headers(), json={})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary_ok"] is False
    assert body["checks"]["vectorai_enabled"]["status"] == "disabled"


def test_vector_diagnostics_happy_path_with_fake_adapter(client, monkeypatch):
    from app.api.v1.routes import admin_vector as route_mod

    class FakeClient:
        def __init__(self, store: dict[int, dict]):
            self.store = store

        def collection_exists(self, name: str) -> bool:
            return True

        def describe_collection(self, collection_name: str):
            return {"name": collection_name, "dimension": 4}

        def get_stats(self, collection_name: str):
            return {"indexed_vectors": len(self.store)}

        def get_state(self, collection_name: str):
            return {"status": "ready"}

        def get(self, collection_name: str, id: int):
            item = self.store[id]
            return item["vector"], item["payload"]

        def delete(self, collection_name: str, id: int):
            self.store.pop(id, None)

    class FakeAdapter:
        def __init__(self, db, config):
            self._db = db
            self._config = config
            self.collection_name = config.collection_name
            self._store: dict[int, dict] = {}
            self._client = FakeClient(self._store)

        def healthcheck(self) -> bool:
            return True

        def ensure_collection(self) -> None:
            return None

        def _require_client(self):
            return self._client

        def flush(self) -> None:
            return None

        def probe_metadata_filtering_support(self) -> bool:
            return True

        def _call_with_collection_fallback(self, method_name: str, /, *args, **kwargs):
            if method_name == "upsert":
                point_id = kwargs["id"]
                self._store[int(point_id)] = {
                    "vector": kwargs["vector"],
                    "payload": kwargs.get("payload") or {},
                }
                return None
            if method_name == "batch_upsert":
                points = kwargs.get("points") or args[0]
                for point in points:
                    self._store[int(point["id"])] = {
                        "vector": point["vector"],
                        "payload": point.get("payload") or {},
                    }
                return None
            if method_name == "search":
                return [
                    {
                        "id": point_id,
                        "score": 0.99,
                        "payload": point["payload"],
                    }
                    for point_id, point in self._store.items()
                ]
            if method_name == "delete":
                self._store.pop(int(kwargs["id"]), None)
                return None
            raise RuntimeError(f"Unexpected method {method_name}")

    monkeypatch.setattr(settings, "vectorai_enabled", True)
    monkeypatch.setattr(settings, "vectorai_address", "127.0.0.1:50051")
    monkeypatch.setattr(settings, "vectorai_collection_name", "user_profiles_embed_v1_test")
    monkeypatch.setattr(settings, "vectorai_metric", "COSINE")
    monkeypatch.setattr(settings, "vectorai_dimension", 4)
    monkeypatch.setattr(settings, "vectorai_supports_metadata_filtering", False)
    monkeypatch.setattr(route_mod, "ActianVectorStoreAdapter", FakeAdapter)

    response = client.post(
        "/api/v1/admin/vector/diagnostics",
        headers=_admin_headers(),
        json={
            "poll_seconds": 0.2,
            "poll_interval_seconds": 0.01,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary_ok"] is True
    assert body["checks"]["healthcheck"]["ok"] is True
    assert body["checks"]["probe_upsert_get"]["ok"] is True
    assert body["checks"]["probe_search_visibility"]["ok"] is True
    assert body["checks"]["probe_metadata_filtering"]["ok"] is True
