from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.vector_index import (
    delete_user_vector_point_id as delete_point_mapping,
    get_user_vector_point_id,
    get_user_vector_point_id_by_point,
    list_user_vector_point_ids_for_user,
    upsert_user_vector_point_id,
)
from app.core.config import Settings
from app.schemas.vector_store import (
    UserProfileEmbeddingRecord,
    UserProfileVectorMetadata,
    UserProfileVectorMatch,
    UserProfileVectorQuery,
)
from app.models.vector_index import UserVectorPointId
from app.services.vector_store import VectorStoreAdapter

try:
    from cortex import CortexClient  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    CortexClient = None  # type: ignore[assignment]


ACTIAN_PROVIDER = "actian"
DEFAULT_ACTIAN_METRIC = "COSINE"


@dataclass(frozen=True)
class ActianVectorStoreConfig:
    address: str
    api_key: str | None = None
    collection_name: str = "user_profiles_embed_v1"
    metric: str = DEFAULT_ACTIAN_METRIC
    dimension: int | None = None
    supports_metadata_filtering: bool = False
    batch_upsert_size: int = 100
    request_timeout_seconds: float | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "ActianVectorStoreConfig":
        return cls(
            address=settings.vectorai_address,
            api_key=settings.vectorai_api_key,
            collection_name=settings.vectorai_collection_name,
            metric=settings.vectorai_metric,
            dimension=settings.vectorai_dimension,
            supports_metadata_filtering=settings.vectorai_supports_metadata_filtering,
            batch_upsert_size=settings.vectorai_batch_upsert_size,
            request_timeout_seconds=settings.vectorai_request_timeout_seconds,
        )


class ActianVectorStoreAdapter(VectorStoreAdapter):
    """Actian/VectorAI adapter skeleton.

    Notes:
    - Uses Postgres `user_vector_point_ids` to map UUID user IDs to SDK integer point IDs.
    - Metadata filtering support is feature-flagged until verified against the running server image.
    - The concrete Cortex SDK method calls are intentionally conservative and may need minor
      signature adjustments once we pin the SDK version in this repo.
    """

    def __init__(
        self,
        *,
        db: Session,
        config: ActianVectorStoreConfig,
        client: Any | None = None,
    ) -> None:
        self._db = db
        self._config = config
        self._client = client
        self._client_connected = client is not None

    @property
    def provider(self) -> str:
        return ACTIAN_PROVIDER

    @property
    def collection_name(self) -> str:
        return self._config.collection_name

    def _require_client(self) -> Any:
        if self._client is not None:
            return self._client
        if CortexClient is None:
            raise RuntimeError(
                "cortex SDK is not installed. Install the Actian/VectorAI Python client to use ActianVectorStoreAdapter."
            )
        kwargs: dict[str, Any] = {"address": self._config.address}
        if self._config.api_key:
            kwargs["api_key"] = self._config.api_key
        # Keep constructor usage minimal until SDK version is pinned in pyproject.
        self._client = CortexClient(**kwargs)
        if hasattr(self._client, "connect"):
            self._client.connect()
            self._client_connected = True
        return self._client

    def _call_with_collection_fallback(self, method_name: str, /, *args: Any, **kwargs: Any) -> Any:
        """Call Cortex SDK methods across minor signature differences.

        Some SDK versions require `collection_name` while others bind collection context elsewhere.
        We try the direct call first, then retry with `collection_name`.
        """

        client = self._require_client()
        method = getattr(client, method_name, None)
        if method is None:
            raise RuntimeError(f"Unsupported Cortex client: {method_name} not available")

        try:
            return method(*args, **kwargs)
        except TypeError:
            if "collection_name" in kwargs:
                raise
            return method(*args, collection_name=self.collection_name, **kwargs)

    def healthcheck(self) -> bool:
        client = self._require_client()
        try:
            # Prefer a lightweight operation. `list_collections()` is documented in examples/docs.
            if hasattr(client, "list_collections"):
                client.list_collections()
            elif hasattr(client, "get_collection_info"):
                self._call_with_collection_fallback("get_collection_info")
            else:
                raise RuntimeError("Unsupported Cortex client: no healthcheck-capable method found")
            return True
        except Exception:
            return False

    def ensure_collection(self) -> None:
        """Create the target collection if it does not exist.

        This is a best-effort helper for local/dev usage. It requires `dimension` in config.
        """

        client = self._require_client()
        if self._config.dimension is None:
            raise ValueError("Actian collection dimension is required to create a collection")

        if hasattr(client, "collection_exists"):
            try:
                if client.collection_exists(self.collection_name):
                    return
            except TypeError:
                # Fall through to create attempt if the signature differs more than expected.
                pass

        try:
            if hasattr(client, "create_collection"):
                try:
                        client.create_collection(
                            name=self.collection_name,
                            dimension=self._config.dimension,
                            distance_metric=self._config.metric,
                        )
                except TypeError:
                    try:
                        client.create_collection(
                            collection_name=self.collection_name,
                            dimension=self._config.dimension,
                            distance_metric=self._config.metric,
                        )
                    except TypeError:
                        client.create_collection(
                            self.collection_name,
                            self._config.dimension,
                            self._config.metric,
                        )
                return
        except Exception as exc:  # pragma: no cover - SDK/environment dependent
            # If create is not idempotent on the server and collection already exists, the caller
            # can ignore provider-specific "already exists" errors at a higher layer.
            raise RuntimeError(f"Failed to create Actian collection '{self.collection_name}': {exc}") from exc

        raise RuntimeError("Unsupported Cortex client: create_collection not available")

    def flush(self) -> None:
        client = self._require_client()
        if hasattr(client, "flush"):
            try:
                client.flush(self.collection_name)
            except TypeError:
                try:
                    client.flush(collection_name=self.collection_name)
                except TypeError:
                    client.flush()

    def probe_metadata_filtering_support(self) -> bool:
        """Feature probe for SDK/server-side filtered search support.

        Returns True only if a filtered search executes successfully against the current collection.
        This does not guarantee semantic correctness of every filter operator, but it detects whether
        filtered search is accepted in the current SDK/server combination.
        """

        client = self._require_client()
        if not hasattr(client, "search"):
            return False

        probe_vector: list[float]
        if self._config.dimension is not None:
            probe_vector = [0.0] * self._config.dimension
        else:
            # We need a vector shape to call search. If dimension is unknown, the probe can't run safely.
            return False

        try:
            from cortex.filters.dsl import Field, Filter  # type: ignore
        except Exception:
            return False

        # Probe a simple scalar payload field that exists in all of our stored records.
        probe_filter = Filter().must(Field("entity_type").eq("user_profile"))
        kwargs: dict[str, Any] = {
            "query": probe_vector,
            "top_k": 1,
            "filter": probe_filter,
            "with_payload": False,
        }

        try:
            self._call_with_collection_fallback("search", **kwargs)
            return True
        except TypeError:
            try:
                kwargs["vector"] = kwargs.pop("query")
                self._call_with_collection_fallback("search", **kwargs)
                return True
            except Exception:
                return False
        except Exception:
            return False

    def _next_point_id(self) -> int:
        """Temporary allocator for integer point IDs.

        This is sufficient for local/dev integration tests and single-writer flows.
        Replace with a DB sequence or transactional allocator before concurrent production writes.
        """

        # Scan existing mappings for this provider/collection and increment max.
        # This is intentionally simple for the adapter skeleton phase.
        stmt = (
            select(func.max(UserVectorPointId.point_id))
            .where(UserVectorPointId.provider == self.provider)
            .where(UserVectorPointId.collection_name == self.collection_name)
        )
        max_point_id = self._db.scalar(stmt)
        return 1 if max_point_id is None else int(max_point_id) + 1

    def _point_id_for_record(self, record: UserProfileEmbeddingRecord) -> int:
        user_uuid = UUID(record.user_id)
        existing = get_user_vector_point_id(
            self._db,
            user_id=user_uuid,
            provider=self.provider,
            embedding_version=record.embedding_version,
        )
        if existing is not None:
            return int(existing.point_id)
        return self._next_point_id()

    def _upsert_mapping(self, record: UserProfileEmbeddingRecord, point_id: int) -> None:
        upsert_user_vector_point_id(
            self._db,
            user_id=UUID(record.user_id),
            provider=self.provider,
            collection_name=self.collection_name,
            embedding_version=record.embedding_version,
            point_id=point_id,
        )

    def upsert_user_profile_embedding(self, record: UserProfileEmbeddingRecord) -> None:
        client = self._require_client()
        point_id = self._point_id_for_record(record)
        payload = {
            "id": record.id,
            "entity_type": record.entity_type,
            "user_id": record.user_id,
            "embedding_version": record.embedding_version,
            "embedding_model": record.embedding_model,
            "preference_profile_version": record.preference_profile_version,
            "source_content_hash": record.source_content_hash,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "metadata": record.metadata.model_dump(),
        }

        if not hasattr(client, "upsert"):
            raise RuntimeError("Unsupported Cortex client: upsert not available")

        # SDK docs indicate `upsert(id: int, vector: list[float], payload: dict | None = None)`
        self._call_with_collection_fallback(
            "upsert", id=point_id, vector=record.vector, payload=payload
        )
        self._upsert_mapping(record, point_id)

    def upsert_user_profile_embeddings(
        self, records: list[UserProfileEmbeddingRecord]
    ) -> None:
        if not records:
            return

        client = self._require_client()
        if hasattr(client, "batch_upsert"):
            # Build points in the shape most SDKs use; adjust once the SDK is pinned.
            points: list[dict[str, Any]] = []
            ids: list[int] = []
            vectors: list[list[float]] = []
            payloads: list[dict[str, Any]] = []
            next_new_point_id: int | None = None
            reserved_point_ids: dict[tuple[str, str], int] = {}
            for record in records:
                reservation_key = (record.user_id, record.embedding_version)
                if reservation_key in reserved_point_ids:
                    point_id = reserved_point_ids[reservation_key]
                else:
                    user_uuid = UUID(record.user_id)
                    existing = get_user_vector_point_id(
                        self._db,
                        user_id=user_uuid,
                        provider=self.provider,
                        embedding_version=record.embedding_version,
                    )
                    if existing is not None:
                        point_id = int(existing.point_id)
                    else:
                        if next_new_point_id is None:
                            next_new_point_id = self._next_point_id()
                        point_id = next_new_point_id
                        next_new_point_id += 1
                    reserved_point_ids[reservation_key] = point_id
                payload = {
                    "id": record.id,
                    "entity_type": record.entity_type,
                    "user_id": record.user_id,
                    "embedding_version": record.embedding_version,
                    "embedding_model": record.embedding_model,
                    "preference_profile_version": record.preference_profile_version,
                    "source_content_hash": record.source_content_hash,
                    "created_at": record.created_at.isoformat(),
                    "updated_at": record.updated_at.isoformat(),
                    "metadata": record.metadata.model_dump(),
                }
                points.append(
                    {
                        "id": point_id,
                        "vector": record.vector,
                        "payload": payload,
                    }
                )
                ids.append(point_id)
                vectors.append(record.vector)
                payloads.append(payload)

            # SDK signatures vary in beta builds. Try known shapes, then fall back to single upserts.
            batch_upsert_ok = False
            try:
                # Shape A: batch_upsert(points=[...])
                self._call_with_collection_fallback("batch_upsert", points=points)
                batch_upsert_ok = True
            except TypeError:
                try:
                    # Shape B: batch_upsert([...])
                    self._call_with_collection_fallback("batch_upsert", points)
                    batch_upsert_ok = True
                except TypeError:
                    method = getattr(client, "batch_upsert")
                    try:
                        # Shape C: batch_upsert(collection_name=..., ids=..., vectors=..., payloads=...)
                        method(
                            collection_name=self.collection_name,
                            ids=ids,
                            vectors=vectors,
                            payloads=payloads,
                        )
                        batch_upsert_ok = True
                    except TypeError:
                        try:
                            # Shape D: batch_upsert(collection_name, ids, vectors, payloads)
                            method(self.collection_name, ids, vectors, payloads)
                            batch_upsert_ok = True
                        except TypeError:
                            try:
                                # Shape E: batch_upsert(collection_name, ids, vectors)
                                method(self.collection_name, ids, vectors)
                                batch_upsert_ok = True
                            except TypeError:
                                batch_upsert_ok = False

            if not batch_upsert_ok:
                for record in records:
                    self.upsert_user_profile_embedding(record)
                return

            for record, point in zip(records, points):
                self._upsert_mapping(record, int(point["id"]))
            return

        for record in records:
            self.upsert_user_profile_embedding(record)

    def query_similar_user_profiles(
        self, query: UserProfileVectorQuery
    ) -> list[UserProfileVectorMatch]:
        client = self._require_client()
        if not hasattr(client, "search"):
            raise RuntimeError("Unsupported Cortex client: search not available")

        search_kwargs: dict[str, Any] = {
            "query": query.query_vector,
            "top_k": query.top_k,
            "with_payload": query.include_metadata,
        }

        # Metadata filtering is intentionally optional until verified on the exact server build.
        if self._config.supports_metadata_filtering and query.filters.model_dump(exclude_none=True):
            # Actian filter syntax to be finalized after a real smoke test against the target image.
            # Keeping this placeholder explicit avoids silent incorrect filtering assumptions.
            raise NotImplementedError(
                "Actian metadata filter translation is not enabled until server-side filter support is verified."
            )

        try:
            raw_results = self._call_with_collection_fallback("search", **search_kwargs)
        except TypeError:
            # Older/newer SDK shape may use `vector=` instead of `query=`.
            search_kwargs["vector"] = search_kwargs.pop("query")
            raw_results = self._call_with_collection_fallback("search", **search_kwargs)
        matches: list[UserProfileVectorMatch] = []
        for result in raw_results:
            result_dict: dict[str, Any] | None = None
            if isinstance(result, dict):
                result_dict = result
            elif hasattr(result, "model_dump"):
                try:
                    result_dict = result.model_dump()  # pydantic v2 model
                except Exception:
                    result_dict = None
            elif hasattr(result, "dict"):
                try:
                    result_dict = result.dict()  # pydantic v1 compatibility
                except Exception:
                    result_dict = None

            payload = getattr(result, "payload", None)
            if payload is None and result_dict is not None:
                payload = result_dict.get("payload")

            point_id = getattr(result, "id", None)
            if point_id is None:
                point_id = getattr(result, "point_id", None)
            if point_id is None and result_dict is not None:
                point_id = result_dict.get("id", result_dict.get("point_id"))

            mapped_user_id: str | None = None
            metadata = None
            if payload:
                mapped_user_id = payload.get("user_id")
                md = payload.get("metadata")
                if query.include_metadata and md is not None:
                    metadata = UserProfileVectorMetadata.model_validate(md)

            if mapped_user_id is None and point_id is not None:
                row = get_user_vector_point_id_by_point(
                    self._db,
                    provider=self.provider,
                    collection_name=self.collection_name,
                    point_id=int(point_id),
                )
                if row is None:
                    continue
                mapped_user_id = str(row.user_id)

            if mapped_user_id is None:
                continue
            if mapped_user_id in query.exclude_user_ids:
                continue

            score = getattr(result, "score", None)
            if score is None and result_dict is not None:
                score = result_dict.get("score", result_dict.get("distance"))
            matches.append(
                UserProfileVectorMatch(
                    id=str(point_id) if point_id is not None else f"actian:{mapped_user_id}",
                    user_id=mapped_user_id,
                    score=float(score) if score is not None else 0.0,
                    metadata=metadata if query.include_metadata else None,
                )
            )
        return matches

    def delete_user_profile_embedding(
        self, *, user_id: str, embedding_version: str
    ) -> bool:
        client = self._require_client()
        row = get_user_vector_point_id(
            self._db,
            user_id=UUID(user_id),
            provider=self.provider,
            embedding_version=embedding_version,
        )
        if row is None:
            return False

        if not hasattr(client, "delete"):
            raise RuntimeError("Unsupported Cortex client: delete not available")
        self._call_with_collection_fallback("delete", id=int(row.point_id))

        return delete_point_mapping(
            self._db,
            user_id=UUID(user_id),
            provider=self.provider,
            embedding_version=embedding_version,
        )

    def delete_user_profile_embeddings_for_user(self, *, user_id: str) -> int:
        client = self._require_client()
        deleted = 0
        rows = list_user_vector_point_ids_for_user(
            self._db, user_id=UUID(user_id), provider=self.provider
        )
        for row in rows:
            if not hasattr(client, "delete"):
                raise RuntimeError("Unsupported Cortex client: delete not available")
            self._call_with_collection_fallback("delete", id=int(row.point_id))
            ok = delete_point_mapping(
                self._db,
                user_id=UUID(user_id),
                provider=self.provider,
                embedding_version=row.embedding_version,
            )
            if ok:
                deleted += 1
        return deleted

    @staticmethod
    def build_record(
        *,
        user_id: str,
        vector: list[float],
        embedding_version: str,
        embedding_model: str,
        preference_profile_version: str,
        source_content_hash: str,
        metadata: dict[str, Any],
    ) -> UserProfileEmbeddingRecord:
        """Convenience helper for adapter callers/tests.

        The actual embedding pipeline can bypass this and build `UserProfileEmbeddingRecord` directly.
        """
        from app.schemas.vector_store import UserProfileVectorMetadata
        from app.services.vector_store import user_profile_embedding_record_id

        now = datetime.now(timezone.utc)
        return UserProfileEmbeddingRecord(
            id=user_profile_embedding_record_id(user_id, embedding_version),
            user_id=user_id,
            vector=vector,
            embedding_version=embedding_version,
            embedding_model=embedding_model,
            preference_profile_version=preference_profile_version,
            source_content_hash=source_content_hash,
            metadata=UserProfileVectorMetadata.model_validate(metadata),
            created_at=now,
            updated_at=now,
        )
