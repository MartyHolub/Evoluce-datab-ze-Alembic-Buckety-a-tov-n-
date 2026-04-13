"""Add bandwidth and billing tracking

Revision ID: 002
Revises: 001
Create Date: 2026-04-13 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "buckets",
        sa.Column(
            "current_storage_bytes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "buckets",
        sa.Column(
            "ingress_bytes", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "buckets",
        sa.Column(
            "egress_bytes", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "buckets",
        sa.Column(
            "internal_transfer_bytes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "buckets",
        sa.Column(
            "count_read_requests",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "buckets",
        sa.Column(
            "count_write_requests",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("buckets", "count_write_requests")
    op.drop_column("buckets", "count_read_requests")
    op.drop_column("buckets", "internal_transfer_bytes")
    op.drop_column("buckets", "egress_bytes")
    op.drop_column("buckets", "ingress_bytes")
    op.drop_column("buckets", "current_storage_bytes")
