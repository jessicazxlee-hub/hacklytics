"""add user vector point id mapping table

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-02-22 18:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_vector_point_ids",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("collection_name", sa.String(length=128), nullable=False),
        sa.Column("embedding_version", sa.String(length=128), nullable=False),
        sa.Column("point_id", sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "embedding_version",
            name="uq_user_vector_point_ids_user_provider_embedding_version",
        ),
        sa.UniqueConstraint(
            "provider",
            "collection_name",
            "point_id",
            name="uq_user_vector_point_ids_provider_collection_point",
        ),
    )
    op.create_index(
        op.f("ix_user_vector_point_ids_user_id"),
        "user_vector_point_ids",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_vector_point_ids_provider"),
        "user_vector_point_ids",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_vector_point_ids_collection_name"),
        "user_vector_point_ids",
        ["collection_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_vector_point_ids_embedding_version"),
        "user_vector_point_ids",
        ["embedding_version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_user_vector_point_ids_embedding_version"),
        table_name="user_vector_point_ids",
    )
    op.drop_index(
        op.f("ix_user_vector_point_ids_collection_name"),
        table_name="user_vector_point_ids",
    )
    op.drop_index(op.f("ix_user_vector_point_ids_provider"), table_name="user_vector_point_ids")
    op.drop_index(op.f("ix_user_vector_point_ids_user_id"), table_name="user_vector_point_ids")
    op.drop_table("user_vector_point_ids")

