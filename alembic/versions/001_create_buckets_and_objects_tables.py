"""Create buckets and objects tables

Revision ID: 001
Revises:
Create Date: 2026-04-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buckets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_buckets_id"), "buckets", ["id"])
    op.create_index(op.f("ix_buckets_name"), "buckets", ["name"])

    op.create_table(
        "objects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "bucket_id",
            sa.Integer(),
            sa.ForeignKey("buckets.id"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
    )
    op.create_index(op.f("ix_objects_id"), "objects", ["id"])
    op.create_index(op.f("ix_objects_bucket_id"), "objects", ["bucket_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_objects_bucket_id"), table_name="objects")
    op.drop_index(op.f("ix_objects_id"), table_name="objects")
    op.drop_table("objects")
    op.drop_index(op.f("ix_buckets_name"), table_name="buckets")
    op.drop_index(op.f("ix_buckets_id"), table_name="buckets")
    op.drop_table("buckets")
