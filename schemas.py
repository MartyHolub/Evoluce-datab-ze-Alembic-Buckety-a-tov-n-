from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Bucket Schemas ---

class BucketCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Unique bucket name")


class BucketResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BillingResponse(BaseModel):
    bucket_id: int
    bucket_name: str
    current_storage_bytes: int
    ingress_bytes: int
    egress_bytes: int
    internal_transfer_bytes: int
    count_write_requests: int
    count_read_requests: int

    model_config = {"from_attributes": True}


# --- S3Object Schemas ---

class ObjectCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=255, description="Object key/filename")
    size: int = Field(..., ge=0, description="Size of the object in bytes")
    content_type: str = Field(default="application/octet-stream", max_length=100)


class ObjectResponse(BaseModel):
    id: int
    key: str
    size: int
    content_type: str
    bucket_id: int
    is_deleted: bool

    model_config = {"from_attributes": True}


class ObjectListResponse(BaseModel):
    id: int
    key: str
    size: int
    content_type: str
    bucket_id: int

    model_config = {"from_attributes": True}
