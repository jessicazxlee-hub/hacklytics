from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, require_admin_key
from app.crud.user import get_user_by_email
from app.crud.vector_index import get_user_vector_point_id
from app.models.user import User
from app.schemas.admin_embeddings import (
    AdminEmbeddingUpsertBatchRequest,
    AdminEmbeddingUpsertBatchResponse,
    AdminEmbeddingUpsertByEmailRequest,
    AdminEmbeddingUpsertRequest,
    AdminEmbeddingUpsertResponse,
    AdminEmbeddingUpsertResultRead,
)
from app.services.actian_vector_store import ActianVectorStoreAdapter, ActianVectorStoreConfig
from app.services.embeddings import (
    USER_PROFILE_EMBEDDING_VERSION,
    FakeEmbedder,
    upsert_user_profile_embeddings_batch,
    upsert_user_profile_embedding,
)

router = APIRouter(
    prefix="/admin/embeddings",
    tags=["admin-embeddings"],
    dependencies=[Depends(require_admin_key)],
)


def _ensure_vectorai_enabled() -> None:
    if not settings.vectorai_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VECTORAI_ENABLED is false",
        )


def _get_user_or_404(db: Session, user_id: UUID) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _fake_embedder_dimension(payload: AdminEmbeddingUpsertRequest, cfg: ActianVectorStoreConfig) -> int:
    dimension = payload.fake_dimension_override or cfg.dimension
    if dimension is None or dimension <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vector dimension is required. Set VECTORAI_DIMENSION or fake_dimension_override.",
        )
    return dimension


def _perform_upsert(
    *,
    db: Session,
    user: User,
    payload: AdminEmbeddingUpsertRequest,
) -> AdminEmbeddingUpsertResponse:
    _ensure_vectorai_enabled()

    cfg = ActianVectorStoreConfig.from_settings(settings)
    adapter = ActianVectorStoreAdapter(db=db, config=cfg)
    if payload.ensure_collection:
        try:
            adapter.ensure_collection()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    dimension = _fake_embedder_dimension(payload, cfg)
    embedder = FakeEmbedder(dimension=dimension)
    embedding_version = payload.embedding_version or USER_PROFILE_EMBEDDING_VERSION

    result = upsert_user_profile_embedding(
        db,
        user_id=user.id,
        vector_store=adapter,
        embedder=embedder,
        embedding_version=embedding_version,
    )

    if payload.flush and hasattr(adapter, "flush"):
        adapter.flush()

    point_mapping = get_user_vector_point_id(
        db,
        user_id=user.id,
        provider=adapter.provider,
        embedding_version=result.embedding_version,
    )
    warnings: list[str] = []
    if point_mapping is None:
        warnings.append("No point-id mapping row found after upsert")

    return AdminEmbeddingUpsertResponse(
        user_id=user.id,
        email=user.email,
        provider=adapter.provider,
        collection_name=adapter.collection_name,
        point_id=point_mapping.point_id if point_mapping is not None else None,
        upsert_result=AdminEmbeddingUpsertResultRead(
            user_id=result.user_id,
            record_id=result.record_id,
            embedding_version=result.embedding_version,
            embedding_model=result.embedding_model,
            preference_profile_version=result.preference_profile_version,
            source_content_hash=result.source_content_hash,
            vector_dimension=result.vector_dimension,
        ),
        warnings=warnings,
    )


def _resolve_batch_users(db: Session, payload: AdminEmbeddingUpsertBatchRequest) -> list[User]:
    users_by_id: dict[UUID, User] = {}

    if payload.user_ids:
        rows = list(db.scalars(select(User).where(User.id.in_(payload.user_ids))).all())
        found = {row.id: row for row in rows}
        missing = [str(user_id) for user_id in payload.user_ids if user_id not in found]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Users not found: {', '.join(missing)}",
            )
        for user_id in payload.user_ids:
            users_by_id[user_id] = found[user_id]

    if payload.emails:
        normalized = [email.lower() for email in payload.emails]
        rows = list(db.scalars(select(User).where(User.email.in_(normalized))).all())
        found = {row.email.lower(): row for row in rows}
        missing = [email for email in normalized if email not in found]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Users not found: {', '.join(missing)}",
            )
        for email in normalized:
            row = found[email]
            users_by_id.setdefault(row.id, row)

    if users_by_id:
        users = list(users_by_id.values())
        users.sort(key=lambda u: (u.created_at, str(u.id)))
        return users

    stmt = select(User)
    if payload.only_discoverable:
        stmt = stmt.where(User.discoverable.is_(True))
    if payload.mode == "in_person":
        stmt = stmt.where(User.open_to_meetups.is_(True))
    elif payload.mode == "chat_only":
        stmt = stmt.where(User.open_to_meetups.is_(False))
    stmt = stmt.order_by(User.created_at.asc(), User.id.asc())
    if payload.limit is not None:
        stmt = stmt.limit(payload.limit)
    return list(db.scalars(stmt).all())


def _perform_batch_upsert(
    *,
    db: Session,
    payload: AdminEmbeddingUpsertBatchRequest,
) -> AdminEmbeddingUpsertBatchResponse:
    _ensure_vectorai_enabled()
    cfg = ActianVectorStoreConfig.from_settings(settings)
    adapter = ActianVectorStoreAdapter(db=db, config=cfg)
    if payload.ensure_collection:
        try:
            adapter.ensure_collection()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    users = _resolve_batch_users(db, payload)
    dimension = _fake_embedder_dimension(payload, cfg)
    embedder = FakeEmbedder(dimension=dimension)
    embedding_version = payload.embedding_version or USER_PROFILE_EMBEDDING_VERSION

    results = upsert_user_profile_embeddings_batch(
        db,
        user_ids=[u.id for u in users],
        vector_store=adapter,
        embedder=embedder,
        embedding_version=embedding_version,
    )
    if payload.flush and hasattr(adapter, "flush"):
        adapter.flush()

    users_by_uuid = {u.id: u for u in users}
    response_rows: list[AdminEmbeddingUpsertResponse] = []
    warnings: list[str] = []
    for result in results:
        user = users_by_uuid[result.user_id]
        point_mapping = get_user_vector_point_id(
            db,
            user_id=user.id,
            provider=adapter.provider,
            embedding_version=result.embedding_version,
        )
        row_warnings: list[str] = []
        if point_mapping is None:
            row_warnings.append("No point-id mapping row found after upsert")
            warnings.append(f"Missing point-id mapping for {user.email}")
        response_rows.append(
            AdminEmbeddingUpsertResponse(
                user_id=user.id,
                email=user.email,
                provider=adapter.provider,
                collection_name=adapter.collection_name,
                point_id=point_mapping.point_id if point_mapping is not None else None,
                upsert_result=AdminEmbeddingUpsertResultRead(
                    user_id=result.user_id,
                    record_id=result.record_id,
                    embedding_version=result.embedding_version,
                    embedding_model=result.embedding_model,
                    preference_profile_version=result.preference_profile_version,
                    source_content_hash=result.source_content_hash,
                    vector_dimension=result.vector_dimension,
                ),
                warnings=row_warnings,
            )
        )

    return AdminEmbeddingUpsertBatchResponse(
        selected_count=len(users),
        upserted_count=len(response_rows),
        provider=adapter.provider,
        collection_name=adapter.collection_name,
        embedding_version=embedding_version,
        results=response_rows,
        warnings=warnings,
    )


@router.post("/upsert-batch", response_model=AdminEmbeddingUpsertBatchResponse)
def admin_upsert_embeddings_batch(
    payload: AdminEmbeddingUpsertBatchRequest,
    db: Session = Depends(get_db),
) -> AdminEmbeddingUpsertBatchResponse:
    return _perform_batch_upsert(db=db, payload=payload)


@router.post("/users/by-email/upsert", response_model=AdminEmbeddingUpsertResponse)
def admin_upsert_user_embedding_by_email(
    payload: AdminEmbeddingUpsertByEmailRequest,
    db: Session = Depends(get_db),
) -> AdminEmbeddingUpsertResponse:
    user = get_user_by_email(db, payload.email.lower())
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _perform_upsert(db=db, user=user, payload=payload)


@router.post("/users/{user_id}/upsert", response_model=AdminEmbeddingUpsertResponse)
def admin_upsert_user_embedding(
    user_id: UUID,
    payload: AdminEmbeddingUpsertRequest,
    db: Session = Depends(get_db),
) -> AdminEmbeddingUpsertResponse:
    user = _get_user_or_404(db, user_id)
    return _perform_upsert(db=db, user=user, payload=payload)
