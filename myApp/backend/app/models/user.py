from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "budget_min IS NULL OR budget_max IS NULL OR budget_min <= budget_max",
            name="ck_users_budget_range",
        ),
    ) 

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    firebase_uid: Mapped[str | None] = mapped_column(String(128), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    auth_provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="firebase",
        server_default="firebase",
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    neighborhood: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geohash: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)

    budget_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    diet_tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"),
        nullable=False,
        default=list,
    )
    vibe_tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"),
        nullable=False,
        default=list,
    )

    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    discoverable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    open_to_meetups: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

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
