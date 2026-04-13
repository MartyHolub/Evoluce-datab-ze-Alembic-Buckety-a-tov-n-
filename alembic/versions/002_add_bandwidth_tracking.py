"""Add bandwidth and request tracking columns to buckets

Revision ID: 002_add_bandwidth
Revises: 001_create_buckets
Create Date: 2026-04-13 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_add_bandwidth"
down_revision: Union[str, None] = "001_create_buckets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add bandwidth tracking columns to buckets table
    op.add_column("buckets", sa.Column("current_storage_bytes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("buckets", sa.Column("ingress_bytes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("buckets", sa.Column("egress_bytes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("buckets", sa.Column("internal_transfer_bytes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("buckets", sa.Column("count_read_requests", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("buckets", sa.Column("count_write_requests", sa.Integer(), nullable=False, server_default="0"))

def downgrade() -> None:
    # Remove bandwidth tracking columns from buckets table
    op.drop_column("buckets", "count_write_requests")
    op.drop_column("buckets", "count_read_requests")
    op.drop_column("buckets", "internal_transfer_bytes")
    op.drop_column("buckets", "egress_bytes")
    op.drop_column("buckets", "ingress_bytes")
    op.drop_column("buckets", "current_storage_bytes")