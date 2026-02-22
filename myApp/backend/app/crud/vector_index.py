from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vector_index import UserVectorPointId


def get_user_vector_point_id(
    db: Session,
    *,
    user_id: UUID,
    provider: str,
    embedding_version: str,
) -> UserVectorPointId | None:
    stmt = (
        select(UserVectorPointId)
        .where(UserVectorPointId.user_id == user_id)
        .where(UserVectorPointId.provider == provider)
        .where(UserVectorPointId.embedding_version == embedding_version)
    )
    return db.scalar(stmt)


def get_user_vector_point_id_by_point(
    db: Session,
    *,
    provider: str,
    collection_name: str,
    point_id: int,
) -> UserVectorPointId | None:
    stmt = (
        select(UserVectorPointId)
        .where(UserVectorPointId.provider == provider)
        .where(UserVectorPointId.collection_name == collection_name)
        .where(UserVectorPointId.point_id == point_id)
    )
    return db.scalar(stmt)


def list_user_vector_point_ids_for_user(
    db: Session,
    *,
    user_id: UUID,
    provider: str | None = None,
) -> list[UserVectorPointId]:
    stmt = select(UserVectorPointId).where(UserVectorPointId.user_id == user_id)
    if provider is not None:
        stmt = stmt.where(UserVectorPointId.provider == provider)
    stmt = stmt.order_by(UserVectorPointId.embedding_version.asc(), UserVectorPointId.point_id.asc())
    return list(db.scalars(stmt).all())


def create_user_vector_point_id(
    db: Session,
    *,
    user_id: UUID,
    provider: str,
    collection_name: str,
    embedding_version: str,
    point_id: int,
) -> UserVectorPointId:
    row = UserVectorPointId(
        user_id=user_id,
        provider=provider,
        collection_name=collection_name,
        embedding_version=embedding_version,
        point_id=point_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_user_vector_point_id(
    db: Session,
    row: UserVectorPointId,
    *,
    collection_name: str | None = None,
    point_id: int | None = None,
) -> UserVectorPointId:
    if collection_name is not None:
        row.collection_name = collection_name
    if point_id is not None:
        row.point_id = point_id
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def upsert_user_vector_point_id(
    db: Session,
    *,
    user_id: UUID,
    provider: str,
    collection_name: str,
    embedding_version: str,
    point_id: int,
) -> UserVectorPointId:
    existing = get_user_vector_point_id(
        db,
        user_id=user_id,
        provider=provider,
        embedding_version=embedding_version,
    )
    if existing is None:
        return create_user_vector_point_id(
            db,
            user_id=user_id,
            provider=provider,
            collection_name=collection_name,
            embedding_version=embedding_version,
            point_id=point_id,
        )
    return update_user_vector_point_id(
        db,
        existing,
        collection_name=collection_name,
        point_id=point_id,
    )


def delete_user_vector_point_id(
    db: Session,
    *,
    user_id: UUID,
    provider: str,
    embedding_version: str,
) -> bool:
    existing = get_user_vector_point_id(
        db,
        user_id=user_id,
        provider=provider,
        embedding_version=embedding_version,
    )
    if existing is None:
        return False
    db.delete(existing)
    db.commit()
    return True

