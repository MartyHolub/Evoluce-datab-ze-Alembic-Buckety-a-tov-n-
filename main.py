import os
from typing import List

import aiofiles
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from database import engine, get_db, Base
from models import Bucket, Object
from schemas import (
    BucketCreate,
    BucketResponse,
    ObjectResponse,
    ObjectListResponse,
    BillingResponse,
    ErrorResponse,
)

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

app = FastAPI(title="Cloud Object Storage", version="1.0.0")


# ── Middleware: detect X-Internal-Source header ──────────────────

class InternalSourceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.is_internal = (
            request.headers.get("X-Internal-Source", "").lower() == "true"
        )
        response = await call_next(request)
        return response


app.add_middleware(InternalSourceMiddleware)


# ── Bucket endpoints ────────────────────────────────────────────

@app.post("/buckets/", response_model=BucketResponse, status_code=201)
def create_bucket(bucket: BucketCreate, db: Session = Depends(get_db)):
    existing = db.query(Bucket).filter(Bucket.name == bucket.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bucket already exists")
    db_bucket = Bucket(name=bucket.name)
    db.add(db_bucket)
    db.commit()
    db.refresh(db_bucket)
    return db_bucket


@app.get("/buckets/", response_model=List[BucketResponse])
def list_buckets(db: Session = Depends(get_db)):
    return db.query(Bucket).all()


@app.get(
    "/buckets/{bucket_id}/",
    response_model=BucketResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_bucket(bucket_id: int, db: Session = Depends(get_db)):
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return bucket


# ── Object endpoints ────────────────────────────────────────────

@app.post(
    "/buckets/{bucket_id}/objects/upload",
    response_model=ObjectResponse,
    status_code=201,
)
async def upload_object(
    bucket_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    x_user_id: str = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    bucket_dir = os.path.join(STORAGE_DIR, str(bucket_id))
    os.makedirs(bucket_dir, exist_ok=True)
    file_path = os.path.join(bucket_dir, file.filename)

    content = await file.read()
    file_size = len(content)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    db_object = Object(
        bucket_id=bucket_id,
        filename=file.filename,
        path=file_path,
        size=file_size,
        user_id=x_user_id,
    )
    db.add(db_object)

    # Update billing counters
    bucket.current_storage_bytes += file_size
    bucket.count_write_requests += 1

    is_internal = getattr(request.state, "is_internal", False) if request else False
    if is_internal:
        bucket.internal_transfer_bytes += file_size
    else:
        bucket.ingress_bytes += file_size

    db.commit()
    db.refresh(db_object)
    return db_object


@app.get(
    "/buckets/{bucket_id}/objects/",
    response_model=ObjectListResponse,
)
def list_objects(bucket_id: int, db: Session = Depends(get_db)):
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    objects = (
        db.query(Object)
        .filter(Object.bucket_id == bucket_id, Object.is_deleted == False)  # noqa: E712
        .all()
    )
    return ObjectListResponse(objects=objects, count=len(objects))


@app.get(
    "/buckets/{bucket_id}/objects/{object_id}/",
    responses={404: {"model": ErrorResponse}},
)
async def download_object(
    bucket_id: int,
    object_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    obj = (
        db.query(Object)
        .filter(
            Object.id == object_id,
            Object.bucket_id == bucket_id,
            Object.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    if not os.path.exists(obj.path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Update billing counters
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    bucket.count_read_requests += 1

    is_internal = getattr(request.state, "is_internal", False)
    if is_internal:
        bucket.internal_transfer_bytes += obj.size
    else:
        bucket.egress_bytes += obj.size

    db.commit()

    return FileResponse(path=obj.path, filename=obj.filename)


@app.delete(
    "/buckets/{bucket_id}/objects/{object_id}/",
    response_model=ObjectResponse,
    responses={404: {"model": ErrorResponse}},
)
def delete_object(
    bucket_id: int, object_id: int, db: Session = Depends(get_db)
):
    obj = (
        db.query(Object)
        .filter(
            Object.id == object_id,
            Object.bucket_id == bucket_id,
            Object.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    # Soft delete
    obj.is_deleted = True
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    bucket.current_storage_bytes = max(
        0, bucket.current_storage_bytes - obj.size
    )
    db.commit()
    db.refresh(obj)
    return obj


# ── Billing endpoint ────────────────────────────────────────────

@app.get(
    "/buckets/{bucket_id}/billing/",
    response_model=BillingResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_billing(bucket_id: int, db: Session = Depends(get_db)):
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return BillingResponse(
        bucket_id=bucket.id,
        bucket_name=bucket.name,
        current_storage_bytes=bucket.current_storage_bytes,
        ingress_bytes=bucket.ingress_bytes,
        egress_bytes=bucket.egress_bytes,
        internal_transfer_bytes=bucket.internal_transfer_bytes,
        count_read_requests=bucket.count_read_requests,
        count_write_requests=bucket.count_write_requests,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
