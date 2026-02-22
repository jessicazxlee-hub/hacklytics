from __future__ import annotations

import math
import time
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, require_admin_key
from app.schemas.vector_diagnostics import (
    VectorDiagnosticsCheck,
    VectorDiagnosticsConfigSnapshot,
    VectorDiagnosticsRequest,
    VectorDiagnosticsResponse,
)
from app.services.actian_vector_store import ActianVectorStoreAdapter, ActianVectorStoreConfig

router = APIRouter(
    prefix="/admin/vector",
    tags=["admin-vector"],
    dependencies=[Depends(require_admin_key)],
)


def _build_probe_vector(dimension: int) -> list[float]:
    # Non-zero deterministic vector for diagnostics.
    vector = [0.0] * dimension
    vector[0] = 1.0
    if dimension > 1:
        vector[1] = 0.5
    return vector


def _vector_diagnostics(vector: list[float]) -> dict:
    has_nan = any(math.isnan(v) for v in vector)
    has_inf = any(math.isinf(v) for v in vector)
    norm = math.sqrt(sum(v * v for v in vector))
    return {
        "length": len(vector),
        "norm": norm,
        "has_nan": has_nan,
        "has_inf": has_inf,
        "nonzero": norm > 0,
    }


def _point_id_from_result(item) -> int | None:
    if isinstance(item, dict):
        value = item.get("id", item.get("point_id"))
        return int(value) if value is not None else None
    point_id = getattr(item, "point_id", None)
    if point_id is not None:
        return int(point_id)
    value = getattr(item, "id", None)
    if value is not None:
        return int(value)
    return None


def _payload_from_result(item) -> dict | None:
    if isinstance(item, dict):
        return item.get("payload")
    payload = getattr(item, "payload", None)
    if payload is not None:
        return payload
    if hasattr(item, "model_dump"):
        try:
            return item.model_dump().get("payload")
        except Exception:
            return None
    if hasattr(item, "dict"):
        try:
            return item.dict().get("payload")
        except Exception:
            return None
    return None


def _timed_check(name: str, func) -> VectorDiagnosticsCheck:
    started = time.monotonic()
    try:
        result = func()
        elapsed_ms = (time.monotonic() - started) * 1000.0
        if isinstance(result, VectorDiagnosticsCheck):
            if result.elapsed_ms is None:
                result.elapsed_ms = elapsed_ms
            return result
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], bool):
            ok, data = result
            return VectorDiagnosticsCheck(
                ok=ok,
                status="ok" if ok else "failed",
                elapsed_ms=elapsed_ms,
                data=data if isinstance(data, dict) else {"value": data},
            )
        return VectorDiagnosticsCheck(
            ok=True,
            status="ok",
            elapsed_ms=elapsed_ms,
            data=result if isinstance(result, dict) else {"value": result},
        )
    except Exception as exc:  # pragma: no cover - exercised in runtime envs
        elapsed_ms = (time.monotonic() - started) * 1000.0
        return VectorDiagnosticsCheck(
            ok=False,
            status="error",
            elapsed_ms=elapsed_ms,
            detail=f"{type(exc).__name__}: {exc}",
        )


@router.post("/diagnostics", response_model=VectorDiagnosticsResponse)
def run_vector_diagnostics(
    payload: VectorDiagnosticsRequest,
    db: Session = Depends(get_db),
) -> VectorDiagnosticsResponse:
    cfg = ActianVectorStoreConfig.from_settings(settings)
    config_snapshot = VectorDiagnosticsConfigSnapshot(
        vectorai_enabled=settings.vectorai_enabled,
        address=cfg.address,
        collection_name=cfg.collection_name,
        metric=cfg.metric,
        dimension=cfg.dimension,
        supports_metadata_filtering=cfg.supports_metadata_filtering,
        batch_upsert_size=cfg.batch_upsert_size,
        request_timeout_seconds=cfg.request_timeout_seconds,
    )

    checks: dict[str, VectorDiagnosticsCheck] = {}
    warnings: list[str] = []

    if not settings.vectorai_enabled:
        checks["vectorai_enabled"] = VectorDiagnosticsCheck(
            ok=False,
            status="disabled",
            detail="VECTORAI_ENABLED is false",
        )
        return VectorDiagnosticsResponse(
            summary_ok=False,
            config=config_snapshot,
            checks=checks,
            warnings=warnings,
        )

    adapter = ActianVectorStoreAdapter(db=db, config=cfg)

    def _healthcheck_probe():
        healthy = adapter.healthcheck()
        return healthy, {"healthy": healthy}

    checks["healthcheck"] = _timed_check("healthcheck", _healthcheck_probe)

    if payload.ensure_collection:
        checks["ensure_collection"] = _timed_check(
            "ensure_collection", lambda: (True, {"ensured": (adapter.ensure_collection() is None)})
        )

    client = None
    client_check = _timed_check("client_init", lambda: {"client_ready": bool(adapter._require_client())})
    checks["client_init"] = client_check
    if client_check.ok:
        client = adapter._require_client()

    def _collection_method_check(method_name: str) -> VectorDiagnosticsCheck:
        if client is None or not hasattr(client, method_name):
            return VectorDiagnosticsCheck(ok=False, status="unavailable", detail=f"{method_name} not available")

        def _run():
            method = getattr(client, method_name)
            try:
                value = method(adapter.collection_name)
            except TypeError:
                value = method(collection_name=adapter.collection_name)
            if hasattr(value, "model_dump"):
                try:
                    value = value.model_dump()
                except Exception:
                    value = repr(value)
            elif isinstance(value, tuple):
                value = list(value)
            elif not isinstance(value, (dict, list, str, int, float, bool, type(None))):
                value = repr(value)
            return {"value": value}

        return _timed_check(method_name, _run)

    for method_name in ["collection_exists", "describe_collection", "get_collection_info", "get_stats", "get_state"]:
        checks[method_name] = _collection_method_check(method_name)

    probe_dimension = payload.vector_dimension_override or cfg.dimension
    if probe_dimension is None:
        warnings.append("Probe vector dimension unavailable; set VECTORAI_DIMENSION or vector_dimension_override")
        checks["probe_vector"] = VectorDiagnosticsCheck(
            ok=False,
            status="skipped",
            detail="No dimension configured",
        )
    else:
        probe_vector = _build_probe_vector(probe_dimension)
        vector_stats = _vector_diagnostics(probe_vector)
        checks["probe_vector"] = VectorDiagnosticsCheck(
            ok=not (vector_stats["has_nan"] or vector_stats["has_inf"]),
            status="ok",
            data=vector_stats,
        )

        probe_point_id = int(time.time() * 1000) % 2_000_000_000 + 1_000_000_000
        probe_key = uuid4().hex
        probe_payload = {
            "entity_type": "diagnostic_probe",
            "probe_key": probe_key,
            "user_id": f"diagnostic:{probe_key}",
            "metadata": {"diagnostic": True, "probe_key": probe_key},
        }

        if payload.probe_write_get and client is not None:
            def _write_get():
                # Upsert
                if payload.use_batch_upsert and hasattr(client, "batch_upsert"):
                    point = {"id": probe_point_id, "vector": probe_vector, "payload": probe_payload}
                    try:
                        adapter._call_with_collection_fallback("batch_upsert", points=[point])
                    except TypeError:
                        adapter._call_with_collection_fallback("batch_upsert", [point])
                else:
                    adapter._call_with_collection_fallback(
                        "upsert", id=probe_point_id, vector=probe_vector, payload=probe_payload
                    )

                adapter.flush()

                if not hasattr(client, "get"):
                    return False, {"reason": "get not available"}
                try:
                    got_vector, got_payload = client.get(adapter.collection_name, probe_point_id)
                except TypeError:
                    got_vector, got_payload = client.get(
                        collection_name=adapter.collection_name, id=probe_point_id
                    )
                ok = (
                    isinstance(got_vector, list)
                    and len(got_vector) == len(probe_vector)
                    and isinstance(got_payload, dict)
                    and got_payload.get("probe_key") == probe_key
                )
                return ok, {
                    "point_id": probe_point_id,
                    "vector_length": len(got_vector) if got_vector is not None else None,
                    "payload_probe_key": got_payload.get("probe_key") if isinstance(got_payload, dict) else None,
                    "used_batch_upsert": payload.use_batch_upsert,
                }

            checks["probe_upsert_get"] = _timed_check("probe_upsert_get", _write_get)
        else:
            checks["probe_upsert_get"] = VectorDiagnosticsCheck(
                ok=False,
                status="skipped",
                detail="write/get probe disabled or client unavailable",
            )

        if payload.probe_search_visibility and client is not None:
            def _probe_search():
                deadline = time.monotonic() + payload.poll_seconds
                attempts = 0
                last_raw_count = 0
                while time.monotonic() < deadline:
                    attempts += 1
                    try:
                        raw = adapter._call_with_collection_fallback(
                            "search",
                            query=probe_vector,
                            top_k=5,
                            with_payload=True,
                            filter=None,
                        )
                    except TypeError:
                        raw = adapter._call_with_collection_fallback(
                            "search",
                            vector=probe_vector,
                            top_k=5,
                            with_payload=True,
                            filter=None,
                        )
                    raw = list(raw)
                    last_raw_count = len(raw)
                    for item in raw:
                        if _point_id_from_result(item) == probe_point_id:
                            return True, {
                                "visible": True,
                                "attempts": attempts,
                                "raw_count": len(raw),
                                "payload_seen": bool(_payload_from_result(item)),
                            }
                    time.sleep(payload.poll_interval_seconds)
                return False, {
                    "visible": False,
                    "attempts": attempts,
                    "raw_count": last_raw_count,
                    "poll_seconds": payload.poll_seconds,
                }

            checks["probe_search_visibility"] = _timed_check("probe_search_visibility", _probe_search)
        else:
            checks["probe_search_visibility"] = VectorDiagnosticsCheck(
                ok=False,
                status="skipped",
                detail="search probe disabled or client unavailable",
            )

        if payload.probe_metadata_filtering:
            def _filter_probe():
                supported = adapter.probe_metadata_filtering_support()
                return supported, {"supported": supported}

            checks["probe_metadata_filtering"] = _timed_check(
                "probe_metadata_filtering",
                _filter_probe,
            )
        else:
            checks["probe_metadata_filtering"] = VectorDiagnosticsCheck(
                ok=False,
                status="skipped",
                detail="metadata filter probe disabled",
            )

        # Best-effort cleanup of diagnostic point.
        if client is not None and hasattr(client, "delete"):
            checks["probe_cleanup"] = _timed_check(
                "probe_cleanup",
                lambda: (
                    True,
                    {
                        "deleted": (
                            adapter._call_with_collection_fallback("delete", id=probe_point_id)
                            is None
                        )
                    },
                ),
            )
        else:
            checks["probe_cleanup"] = VectorDiagnosticsCheck(
                ok=False,
                status="skipped",
                detail="delete not available",
            )

    required_summary_checks = {
        "vectorai_enabled",
        "healthcheck",
        "client_init",
        "ensure_collection",
        "probe_vector",
        "probe_upsert_get",
        "probe_cleanup",
    }
    summary_ok = True
    for name, check in checks.items():
        if name not in required_summary_checks:
            continue
        if name == "ensure_collection" and not payload.ensure_collection:
            continue
        if name in {"probe_upsert_get", "probe_cleanup"} and not payload.probe_write_get:
            continue
        if not check.ok:
            summary_ok = False
            break

    if "probe_search_visibility" in checks and not checks["probe_search_visibility"].ok:
        warnings.append(
            "Search visibility probe failed; write/get may still be working (known beta behavior on some local images)."
        )

    return VectorDiagnosticsResponse(
        summary_ok=summary_ok,
        config=config_snapshot,
        checks=checks,
        warnings=warnings,
    )
