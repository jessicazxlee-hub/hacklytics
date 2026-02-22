from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GroupMatch(Base):
    __tablename__ = "group_matches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('forming', 'confirmed', 'scheduled', 'completed', 'cancelled', 'expired')",
            name="ck_group_matches_status",
        ),
        CheckConstraint(
            "group_match_mode IN ('in_person', 'chat_only')",
            name="ck_group_matches_mode",
        ),
        CheckConstraint(
            "created_source IN ('system', 'user', 'admin')",
            name="ck_group_matches_created_source",
        ),
        CheckConstraint(
            "group_match_mode <> 'chat_only' OR status NOT IN ('scheduled', 'completed')",
            name="ck_group_matches_chat_only_status",
        ),
        UniqueConstraint("chat_room_key", name="uq_group_matches_chat_room_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="forming",
        server_default="forming",
        index=True,
    )
    group_match_mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="in_person",
        server_default="in_person",
        index=True,
    )
    created_source: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="system",
        server_default="system",
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chat_room_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class GroupMatchMember(Base):
    __tablename__ = "group_match_members"
    __table_args__ = (
        CheckConstraint(
            "status IN ('invited', 'accepted', 'declined', 'left', 'removed', 'replaced')",
            name="ck_group_match_members_status",
        ),
        UniqueConstraint(
            "group_match_id",
            "user_id",
            name="uq_group_match_members_group_user",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    group_match_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("group_matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="invited",
        server_default="invited",
        index=True,
    )
    slot_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class GroupMatchVenue(Base):
    __tablename__ = "group_match_venue"
    __table_args__ = (
        CheckConstraint(
            "venue_kind IN ('restaurant', 'activity', 'cafe', 'bar', 'custom')",
            name="ck_group_match_venue_kind",
        ),
        CheckConstraint(
            "source IN ('internal_restaurants', 'external_api', 'manual')",
            name="ck_group_match_venue_source",
        ),
        UniqueConstraint("group_match_id", name="uq_group_match_venue_group_match_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    group_match_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("group_matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    venue_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    restaurant_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("restaurants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_place_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    address_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    neighborhood_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
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
