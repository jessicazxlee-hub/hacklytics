from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class VectorDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ensure_collection: bool = True
    probe_write_get: bool = True
    probe_search_visibility: bool = True
    probe_metadata_filtering: bool = True
    use_batch_upsert: bool = False
    poll_seconds: float = Field(default=3.0, ge=0.0, le=30.0)
    poll_interval_seconds: float = Field(default=0.1, gt=0.0, le=5.0)
    vector_dimension_override: int | None = Field(default=None, gt=0)


class VectorDiagnosticsCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    status: str
    elapsed_ms: float | None = None
    detail: str | None = None
    data: dict = Field(default_factory=dict)


class VectorDiagnosticsConfigSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vectorai_enabled: bool
    address: str
    collection_name: str
    metric: str
    dimension: int | None
    supports_metadata_filtering: bool
    batch_upsert_size: int
    request_timeout_seconds: float | None


class VectorDiagnosticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = "actian"
    summary_ok: bool
    config: VectorDiagnosticsConfigSnapshot
    checks: dict[str, VectorDiagnosticsCheck]
    warnings: list[str] = Field(default_factory=list)

