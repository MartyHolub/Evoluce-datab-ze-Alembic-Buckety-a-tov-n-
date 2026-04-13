from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from database import Base


class Bucket(Base):
    __tablename__ = "buckets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Bandwidth / billing tracking (added in migration 2)
    current_storage_bytes = Column(Integer, default=0, nullable=False)
    ingress_bytes = Column(Integer, default=0, nullable=False)
    egress_bytes = Column(Integer, default=0, nullable=False)
    internal_transfer_bytes = Column(Integer, default=0, nullable=False)
    count_read_requests = Column(Integer, default=0, nullable=False)
    count_write_requests = Column(Integer, default=0, nullable=False)

    objects = relationship("Object", back_populates="bucket")


class Object(Base):
    __tablename__ = "objects"

    id = Column(Integer, primary_key=True, index=True)
    bucket_id = Column(Integer, ForeignKey("buckets.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(String, nullable=True)

    # Soft delete (added in migration 3)
    is_deleted = Column(Boolean, default=False, nullable=False)

    bucket = relationship("Bucket", back_populates="objects")
