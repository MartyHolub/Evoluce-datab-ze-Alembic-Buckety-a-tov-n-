from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Bucket, S3Object
from schemas import (
    BucketCreate,
    BucketResponse,
    BillingResponse,
    S3ObjectCreate,
    S3ObjectResponse,
    S3ObjectListResponse,
)

app = FastAPI(title="S3-like Object Storage API")


# --- Bucket Endpoints ---


@app.post("/buckets/", response_model=BucketResponse, status_code=201)
def create_bucket(bucket: BucketCreate, db: Session = Depends(get_db)):
    """Create a new bucket."""
    existing = db.query(Bucket).filter(Bucket.name == bucket.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Bucket with this name already exists")

    db_bucket = Bucket(name=bucket.name)
    db.add(db_bucket)
    db.commit()
    db.refresh(db_bucket)

    # Count write request
    db_bucket.count_write_requests += 1
    db.commit()
    db.refresh(db_bucket)

    return db_bucket


@app.get("/buckets/", response_model=list[BucketResponse])
def list_buckets(db: Session = Depends(get_db)):
    """List all buckets."""
    return db.query(Bucket).all()


@app.get("/buckets/{bucket_id}/objects/", response_model=list[S3ObjectListResponse])
def list_bucket_objects(bucket_id: int, db: Session = Depends(get_db)):
    """List all non-deleted objects in a specific bucket."""
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    # Count read request
    bucket.count_read_requests += 1
    db.commit()

    objects = (
        db.query(S3Object)
        .filter(S3Object.bucket_id == bucket_id, S3Object.is_deleted == False)
        .all()
    )
    return objects


@app.get("/buckets/{bucket_id}/billing/", response_model=BillingResponse)
def get_bucket_billing(bucket_id: int, db: Session = Depends(get_db)):
    """Get billing information for a specific bucket."""
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    # Count read request
    bucket.count_read_requests += 1
    db.commit()
    db.refresh(bucket)

    return BillingResponse(
        bucket_id=bucket.id,
        bucket_name=bucket.name,
        current_storage_bytes=bucket.current_storage_bytes,
        ingress_bytes=bucket.ingress_bytes,
        egress_bytes=bucket.egress_bytes,
        internal_transfer_bytes=bucket.internal_transfer_bytes,
        count_write_requests=bucket.count_write_requests,
        count_read_requests=bucket.count_read_requests,
    )


# --- S3Object Endpoints ---


@app.post("/buckets/{bucket_id}/objects/", response_model=S3ObjectResponse, status_code=201)
def upload_object(
    bucket_id: int,
    obj: S3ObjectCreate,
    db: Session = Depends(get_db),
    x_internal_source: Optional[str] = Header(None),
):
    """Upload (create) a new object in a bucket."""
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    db_object = S3Object(
        key=obj.key,
        size=obj.size,
        content_type=obj.content_type,
        bucket_id=bucket_id,
    )
    db.add(db_object)

    # Update billing: storage always increases
    bucket.current_storage_bytes += obj.size

    # Determine if internal or external
    is_internal = x_internal_source and x_internal_source.lower() == "true"
    if is_internal:
        bucket.internal_transfer_bytes += obj.size
    else:
        bucket.ingress_bytes += obj.size

    # Count write request
    bucket.count_write_requests += 1

    db.commit()
    db.refresh(db_object)
    return db_object


@app.get("/objects/{object_id}", response_model=S3ObjectResponse)
def download_object(
    object_id: int,
    db: Session = Depends(get_db),
    x_internal_source: Optional[str] = Header(None),
):
    """Download (read metadata of) an object."""
    obj = db.query(S3Object).filter(S3Object.id == object_id, S3Object.is_deleted == False).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    bucket = db.query(Bucket).filter(Bucket.id == obj.bucket_id).first()

    # Determine if internal or external
    is_internal = x_internal_source and x_internal_source.lower() == "true"
    if is_internal:
        bucket.internal_transfer_bytes += obj.size
    else:
        bucket.egress_bytes += obj.size

    # Count read request
    bucket.count_read_requests += 1

    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/objects/{object_id}", response_model=S3ObjectResponse)
def delete_object(
    object_id: int,
    db: Session = Depends(get_db),
):
    """Soft-delete an object. Sets is_deleted=True instead of removing from DB."""
    obj = db.query(S3Object).filter(S3Object.id == object_id, S3Object.is_deleted == False).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    obj.is_deleted = True

    # Update billing: reduce storage when soft-deleted
    bucket = db.query(Bucket).filter(Bucket.id == obj.bucket_id).first()
    bucket.current_storage_bytes = max(0, bucket.current_storage_bytes - obj.size)

    # Count write request
    bucket.count_write_requests += 1

    db.commit()
    db.refresh(obj)
    return obj


@app.get("/objects/", response_model=list[S3ObjectListResponse])
def list_all_objects(db: Session = Depends(get_db)):
    """List all non-deleted objects across all buckets."""
    return db.query(S3Object).filter(S3Object.is_deleted == False).all()
