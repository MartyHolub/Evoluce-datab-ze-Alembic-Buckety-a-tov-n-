from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Bucket(Base):
    __tablename__ = "buckets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Billing fields (Migration 2)
    current_storage_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    ingress_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    egress_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    internal_transfer_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Request counting (Migration 4)
    count_write_requests: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    count_read_requests: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    objects: Mapped[list["S3Object"]] = relationship("S3Object", back_populates="bucket")


class S3Object(Base):
    __tablename__ = "s3objects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(1024), nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(255), default="application/octet-stream")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Bucket relation (Migration 1)
    bucket_id: Mapped[int] = mapped_column(ForeignKey("buckets.id"), nullable=False)
    bucket: Mapped["Bucket"] = relationship("Bucket", back_populates="objects")

    # Soft delete (Migration 3)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
