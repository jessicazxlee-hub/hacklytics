"""add group match tables

Revision ID: c4d1b2e9a7f3
Revises: 8aa9d6bc2f10
Create Date: 2026-02-22 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c4d1b2e9a7f3"
down_revision: Union[str, Sequence[str], None] = "8aa9d6bc2f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="forming"),
        sa.Column("group_match_mode", sa.String(length=16), nullable=False, server_default="in_person"),
        sa.Column("created_source", sa.String(length=16), nullable=False, server_default="system"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("chat_room_key", sa.String(length=255), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('forming', 'confirmed', 'scheduled', 'completed', 'cancelled', 'expired')",
            name="ck_group_matches_status",
        ),
        sa.CheckConstraint(
            "group_match_mode IN ('in_person', 'chat_only')",
            name="ck_group_matches_mode",
        ),
        sa.CheckConstraint(
            "created_source IN ('system', 'user', 'admin')",
            name="ck_group_matches_created_source",
        ),
        sa.CheckConstraint(
            "group_match_mode <> 'chat_only' OR status NOT IN ('scheduled', 'completed')",
            name="ck_group_matches_chat_only_status",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_room_key", name="uq_group_matches_chat_room_key"),
    )
    op.create_index(op.f("ix_group_matches_status"), "group_matches", ["status"], unique=False)
    op.create_index(op.f("ix_group_matches_group_match_mode"), "group_matches", ["group_match_mode"], unique=False)
    op.create_index(op.f("ix_group_matches_created_by_user_id"), "group_matches", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_group_matches_scheduled_for"), "group_matches", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_group_matches_expires_at"), "group_matches", ["expires_at"], unique=False)

    op.create_table(
        "group_match_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="invited"),
        sa.Column("slot_number", sa.Integer(), nullable=True),
        sa.Column(
            "invited_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('invited', 'accepted', 'declined', 'left', 'removed', 'replaced')",
            name="ck_group_match_members_status",
        ),
        sa.ForeignKeyConstraint(["group_match_id"], ["group_matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_match_id", "user_id", name="uq_group_match_members_group_user"),
    )
    op.create_index(op.f("ix_group_match_members_group_match_id"), "group_match_members", ["group_match_id"], unique=False)
    op.create_index(op.f("ix_group_match_members_user_id"), "group_match_members", ["user_id"], unique=False)
    op.create_index(op.f("ix_group_match_members_status"), "group_match_members", ["status"], unique=False)

    op.create_table(
        "group_match_venue",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("venue_kind", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=True),
        sa.Column("external_place_id", sa.String(length=255), nullable=True),
        sa.Column("name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("address_snapshot", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("neighborhood_snapshot", sa.String(length=255), nullable=True),
        sa.Column("price_level", sa.Integer(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "venue_kind IN ('restaurant', 'activity', 'cafe', 'bar', 'custom')",
            name="ck_group_match_venue_kind",
        ),
        sa.CheckConstraint(
            "source IN ('internal_restaurants', 'external_api', 'manual')",
            name="ck_group_match_venue_source",
        ),
        sa.ForeignKeyConstraint(["group_match_id"], ["group_matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_match_id", name="uq_group_match_venue_group_match_id"),
    )
    op.create_index(op.f("ix_group_match_venue_group_match_id"), "group_match_venue", ["group_match_id"], unique=False)
    op.create_index(op.f("ix_group_match_venue_restaurant_id"), "group_match_venue", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_group_match_venue_external_place_id"), "group_match_venue", ["external_place_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_group_match_venue_external_place_id"), table_name="group_match_venue")
    op.drop_index(op.f("ix_group_match_venue_restaurant_id"), table_name="group_match_venue")
    op.drop_index(op.f("ix_group_match_venue_group_match_id"), table_name="group_match_venue")
    op.drop_table("group_match_venue")

    op.drop_index(op.f("ix_group_match_members_status"), table_name="group_match_members")
    op.drop_index(op.f("ix_group_match_members_user_id"), table_name="group_match_members")
    op.drop_index(op.f("ix_group_match_members_group_match_id"), table_name="group_match_members")
    op.drop_table("group_match_members")

    op.drop_index(op.f("ix_group_matches_expires_at"), table_name="group_matches")
    op.drop_index(op.f("ix_group_matches_scheduled_for"), table_name="group_matches")
    op.drop_index(op.f("ix_group_matches_created_by_user_id"), table_name="group_matches")
    op.drop_index(op.f("ix_group_matches_group_match_mode"), table_name="group_matches")
    op.drop_index(op.f("ix_group_matches_status"), table_name="group_matches")
    op.drop_table("group_matches")
