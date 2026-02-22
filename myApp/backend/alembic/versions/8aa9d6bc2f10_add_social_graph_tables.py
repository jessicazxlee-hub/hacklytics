"""add social graph tables

Revision ID: 8aa9d6bc2f10
Revises: d3f4b8a1c9e2
Create Date: 2026-02-22 11:05:26.020308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "8aa9d6bc2f10"
down_revision: Union[str, Sequence[str], None] = "d3f4b8a1c9e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "friend_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("addressee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint("requester_id <> addressee_id", name="ck_friend_requests_no_self"),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'cancelled')",
            name="ck_friend_requests_status",
        ),
        sa.ForeignKeyConstraint(["addressee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "requester_id",
            "addressee_id",
            name="uq_friend_requests_requester_addressee",
        ),
    )
    op.create_index(op.f("ix_friend_requests_addressee_id"), "friend_requests", ["addressee_id"], unique=False)
    op.create_index(op.f("ix_friend_requests_requester_id"), "friend_requests", ["requester_id"], unique=False)
    op.create_index(
        "ix_friend_requests_addressee_status",
        "friend_requests",
        ["addressee_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_friend_requests_requester_status",
        "friend_requests",
        ["requester_id", "status"],
        unique=False,
    )

    op.create_table(
        "friendships",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("friend_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("user_id <> friend_id", name="ck_friendships_no_self"),
        sa.ForeignKeyConstraint(["friend_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_request_id"], ["friend_requests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "friend_id"),
    )
    op.create_index(op.f("ix_friendships_friend_id"), "friendships", ["friend_id"], unique=False)
    op.create_index(
        op.f("ix_friendships_source_request_id"),
        "friendships",
        ["source_request_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_friendships_source_request_id"), table_name="friendships")
    op.drop_index(op.f("ix_friendships_friend_id"), table_name="friendships")
    op.drop_table("friendships")

    op.drop_index("ix_friend_requests_requester_status", table_name="friend_requests")
    op.drop_index("ix_friend_requests_addressee_status", table_name="friend_requests")
    op.drop_index(op.f("ix_friend_requests_requester_id"), table_name="friend_requests")
    op.drop_index(op.f("ix_friend_requests_addressee_id"), table_name="friend_requests")
    op.drop_table("friend_requests")
