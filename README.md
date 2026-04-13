# Cloud Object Storage – Alembic Migrations

FastAPI-based object storage with SQLAlchemy, Alembic migrations, bandwidth billing, and soft delete.

## Quick Start

```bash
pip install -r requirements.txt
alembic upgrade head
python main.py
```

Open interactive docs at **http://localhost:8000/docs**.

## Project Structure

| File | Description |
|---|---|
| `database.py` | SQLAlchemy engine, `SessionLocal`, `get_db` dependency |
| `models.py` | `Bucket` and `Object` ORM models |
| `schemas.py` | Pydantic validation schemas |
| `main.py` | FastAPI application with all endpoints |
| `alembic.ini` | Alembic configuration (sqlite URL) |
| `alembic/env.py` | Alembic environment with `Base.metadata` for autogenerate |
| `alembic/versions/` | Sequential migration scripts |

## Alembic Migrations

Three sequential migrations evolve the database schema:

| # | File | Description |
|---|---|---|
| 1 | `001_create_buckets_and_objects_tables.py` | Creates `buckets` and `objects` tables with indexes |
| 2 | `002_add_bandwidth_tracking.py` | Adds billing columns to `buckets` (storage, ingress, egress, internal transfer, request counts) |
| 3 | `003_add_soft_delete.py` | Adds `is_deleted` boolean to `objects` |

### Running Migrations

```bash
# Apply all migrations
alembic upgrade head

# Check current revision
alembic current

# Downgrade one step
alembic downgrade -1

# Auto-generate a new migration from model changes
alembic revision --autogenerate -m "description"
```

## API Endpoints

### Buckets

- `POST /buckets/` – Create a bucket (body: `{"name": "..."}`)
- `GET /buckets/` – List all buckets
- `GET /buckets/{bucket_id}/` – Get bucket details

### Objects

- `POST /buckets/{bucket_id}/objects/upload` – Upload a file (multipart form, tracks ingress)
- `GET /buckets/{bucket_id}/objects/` – List objects (excludes soft-deleted)
- `GET /buckets/{bucket_id}/objects/{object_id}/` – Download object (tracks egress)
- `DELETE /buckets/{bucket_id}/objects/{object_id}/` – Soft delete (sets `is_deleted=True`)

### Billing

- `GET /buckets/{bucket_id}/billing/` – Returns storage, ingress, egress, internal transfer bytes, and read/write request counts

## Key Features

- **X-Internal-Source header** – Middleware detects `X-Internal-Source: true` and routes transfer bytes to `internal_transfer_bytes` instead of ingress/egress.
- **Soft delete** – DELETE marks objects as `is_deleted=True`; list endpoints automatically filter them out.
- **Bandwidth tracking** – Every upload increments ingress (or internal), every download increments egress (or internal), and request counts are tracked.
- **X-User-ID header** – Backward-compatible user identification on uploads.
