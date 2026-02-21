"""add display_name and hobby catalog tables

Revision ID: d3f4b8a1c9e2
Revises: 7c8d6e5a2f31
Create Date: 2026-02-21 14:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d3f4b8a1c9e2"
down_revision: Union[str, Sequence[str], None] = "7c8d6e5a2f31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=32), nullable=True))
    op.create_index(op.f("ix_users_display_name"), "users", ["display_name"], unique=False)
    op.execute(
        "CREATE UNIQUE INDEX uq_users_display_name_ci "
        "ON users (lower(display_name)) "
        "WHERE display_name IS NOT NULL"
    )

    op.create_table(
        "hobby_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_hobby_catalog_code"), "hobby_catalog", ["code"], unique=True)

    op.create_table(
        "user_hobbies",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hobby_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["hobby_id"], ["hobby_catalog.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "hobby_id"),
    )
    op.create_index(op.f("ix_user_hobbies_hobby_id"), "user_hobbies", ["hobby_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_hobbies_hobby_id"), table_name="user_hobbies")
    op.drop_table("user_hobbies")

    op.drop_index(op.f("ix_hobby_catalog_code"), table_name="hobby_catalog")
    op.drop_table("hobby_catalog")

    op.execute("DROP INDEX IF EXISTS uq_users_display_name_ci")
    op.drop_index(op.f("ix_users_display_name"), table_name="users")
    op.drop_column("users", "display_name")
