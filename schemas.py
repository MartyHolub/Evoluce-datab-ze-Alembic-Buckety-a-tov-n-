from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ── Bucket schemas ──────────────────────────────────────────────

class BucketCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class BucketResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Object schemas ──────────────────────────────────────────────

class ObjectCreate(BaseModel):
    filename: str
    bucket_id: int
    size: int
    path: str
    user_id: Optional[str] = None


class ObjectResponse(BaseModel):
    id: int
    bucket_id: int
    filename: str
    size: int
    created_at: datetime
    user_id: Optional[str] = None
    is_deleted: bool = False

    model_config = {"from_attributes": True}


class ObjectListResponse(BaseModel):
    objects: List[ObjectResponse]
    count: int


# ── Billing schemas ─────────────────────────────────────────────

class BillingResponse(BaseModel):
    bucket_id: int
    bucket_name: str
    current_storage_bytes: int = 0
    ingress_bytes: int = 0
    egress_bytes: int = 0
    internal_transfer_bytes: int = 0
    count_read_requests: int = 0
    count_write_requests: int = 0

    model_config = {"from_attributes": True}


# ── Error schemas ───────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
