# Evoluce databáze: Alembic, Buckety a Účtování

S3-like objektové úložiště postavené na FastAPI + SQLAlchemy + Alembic.

---

## Požadavky

- Python 3.10+

---

## Instalace a spuštění

### 1. Naklonujte repozitář a přejděte do složky projektu

```bash
git clone <url-repozitáře>
cd <složka-projektu>
```

### 2. Vytvořte a aktivujte virtuální prostředí

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Nainstalujte závislosti

```bash
pip install -r requirements.txt
```

### 4. Aplikujte databázové migrace

Příkaz vytvoří soubor `todo.db` a postupně aplikuje všechny tři migrace:

```bash
alembic upgrade head
```

Výstup by měl vypadat takto:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 307fa68a9bd6, create buckets and objects tables
INFO  [alembic.runtime.migration] Running upgrade 307fa68a9bd6 -> 13c0af6f21f4, add billing columns to buckets
INFO  [alembic.runtime.migration] Running upgrade 13c0af6f21f4 -> 27d41f48cb50, add soft delete and request counting
```

### 5. Spusťte aplikaci

```bash
uvicorn main:app --reload
```

Aplikace poběží na adrese: **http://127.0.0.1:8000**

---

## Interaktivní dokumentace API

Po spuštění jsou dostupné dvě rozhraní:

| Rozhraní | URL |
|----------|-----|
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

---

## Přehled endpointů

| Metoda | URL | Popis |
|--------|-----|-------|
| `POST` | `/buckets/` | Vytvoření nového bucketu |
| `GET` | `/buckets/` | Výpis všech bucketů |
| `GET` | `/buckets/{bucket_id}/objects/` | Výpis objektů v bucketu (bez smazaných) |
| `GET` | `/buckets/{bucket_id}/billing/` | Stav účtu za přenos dat |
| `POST` | `/buckets/{bucket_id}/objects/` | Nahrání objektu do bucketu |
| `GET` | `/objects/{object_id}` | Stažení metadat objektu |
| `DELETE` | `/objects/{object_id}` | Soft delete objektu |

### Interní vs. externí provoz

Pro simulaci interního provozu přidejte do požadavku HTTP hlavičku:

```
X-Internal-Source: true
```

- **Bez hlavičky** → upload počítá do `ingress_bytes`, download do `egress_bytes`
- **S hlavičkou** → přenos se počítá do `internal_transfer_bytes`

---

## Migrace — přehled

| Číslo | Revize | Popis |
|-------|--------|-------|
| 1 | `307fa68a9bd6` | Vytvoření tabulek `buckets` a `objects` |
| 2 | `13c0af6f21f4` | Přidání billing sloupců do `buckets` |
| 3 | `27d41f48cb50` | Soft delete + počítadla API requestů |

Zobrazení historie migrací:

```bash
alembic history
```

Vrácení poslední migrace zpět:

```bash
alembic downgrade -1
```

---

## Příklad použití (curl)

```bash
# Vytvoření bucketu
curl -X POST http://127.0.0.1:8000/buckets/ \
  -H "Content-Type: application/json" \
  -d '{"name": "muj-bucket"}'

# Nahrání objektu (externí)
curl -X POST http://127.0.0.1:8000/buckets/1/objects/ \
  -H "Content-Type: application/json" \
  -d '{"key": "soubor.txt", "size": 1024, "content_type": "text/plain"}'

# Nahrání objektu (interní)
curl -X POST http://127.0.0.1:8000/buckets/1/objects/ \
  -H "Content-Type: application/json" \
  -H "X-Internal-Source: true" \
  -d '{"key": "interni.dat", "size": 2048}'

# Výpis objektů v bucketu
curl http://127.0.0.1:8000/buckets/1/objects/

# Stažení metadat objektu
curl http://127.0.0.1:8000/objects/1

# Zobrazení účtu
curl http://127.0.0.1:8000/buckets/1/billing/

# Soft delete objektu
curl -X DELETE http://127.0.0.1:8000/objects/1
```
