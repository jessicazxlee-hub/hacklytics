from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserVectorPointId(Base):
    __tablename__ = "user_vector_point_ids"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider",
            "embedding_version",
            name="uq_user_vector_point_ids_user_provider_embedding_version",
        ),
        UniqueConstraint(
            "provider",
            "collection_name",
            "point_id",
            name="uq_user_vector_point_ids_provider_collection_point",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    collection_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    embedding_version: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    point_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

