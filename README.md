# S3-like Object Storage API

REST API pro správu bucketů a objektů inspirovaná Amazon S3. Postaveno na **FastAPI**, **SQLAlchemy** a **Alembic** s SQLite databází.

## Požadavky

- Python 3.10+
- pip

## Instalace

1. **Naklonuj repozitář**

   ```bash
   git clone https://github.com/MartyHolub/Evoluce-datab-ze-Alembic-Buckety-a-tov-n-.git
   cd Evoluce-datab-ze-Alembic-Buckety-a-tov-n-
   ```

2. **Vytvoř a aktivuj virtuální prostředí**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / macOS
   venv\Scripts\activate      # Windows
   ```

3. **Nainstaluj závislosti**

   ```bash
   pip install -r requirements.txt
   ```

## Spuštění databázových migrací (Alembic)

Projekt používá Alembic pro správu schématu databáze. Před prvním spuštěním aplikace je potřeba aplikovat migrace:

```bash
alembic upgrade head
```

Tím se vytvoří SQLite soubor `todo.db` a aplikují se všechny migrace:

| Migrace | Popis |
|---|---|
| `6f26749eb79e` | Vytvoření tabulek `buckets` a `s3objects` |
| `b700dc524b4b` | Přidání billing sloupců do `buckets` |
| `fdf484c7e03b` | Přidání soft-delete pro `s3objects` |
| `dcbbc3f9a88c` | Přidání počítání requestů do `buckets` |

### Další užitečné Alembic příkazy

```bash
# Zobrazit aktuální revizi databáze
alembic current

# Zobrazit historii migrací
alembic history

# Vrátit poslední migraci
alembic downgrade -1

# Vytvořit novou migraci (autogenerate)
alembic revision --autogenerate -m "popis zmeny"
```

## Spuštění aplikace

```bash
uvicorn main:app --reload
```

Aplikace poběží na `http://127.0.0.1:8000`.

- **Swagger UI (interaktivní dokumentace):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## API Endpointy

### Buckety

| Metoda | Endpoint | Popis |
|---|---|---|
| `POST` | `/buckets/` | Vytvoření nového bucketu |
| `GET` | `/buckets/` | Výpis všech bucketů |
| `GET` | `/buckets/{bucket_id}/objects/` | Výpis objektů v bucketu |
| `GET` | `/buckets/{bucket_id}/billing/` | Billing informace bucketu |

### Objekty

| Metoda | Endpoint | Popis |
|---|---|---|
| `POST` | `/buckets/{bucket_id}/objects/` | Nahrání objektu do bucketu |
| `GET` | `/objects/{object_id}` | Stažení (metadata) objektu |
| `DELETE` | `/objects/{object_id}` | Soft-delete objektu |
| `GET` | `/objects/` | Výpis všech objektů |

## Příklady použití (curl)

### Vytvoření bucketu

```bash
curl -X POST http://127.0.0.1:8000/buckets/ \
  -H "Content-Type: application/json" \
  -d '{"name": "muj-bucket"}'
```

### Nahrání objektu

```bash
curl -X POST http://127.0.0.1:8000/buckets/1/objects/ \
  -H "Content-Type: application/json" \
  -d '{"key": "soubor.txt", "size": 1024, "content_type": "text/plain"}'
```

### Stažení objektu

```bash
curl http://127.0.0.1:8000/objects/1
```

### Interní transfer (hlavička `X-Internal-Source`)

```bash
curl -X POST http://127.0.0.1:8000/buckets/1/objects/ \
  -H "Content-Type: application/json" \
  -H "X-Internal-Source: true" \
  -d '{"key": "interni.txt", "size": 512}'
```

### Zobrazení billingu

```bash
curl http://127.0.0.1:8000/buckets/1/billing/
```

### Smazání objektu (soft-delete)

```bash
curl -X DELETE http://127.0.0.1:8000/objects/1
```

## Struktura projektu

```
├── main.py            # FastAPI aplikace a endpointy
├── models.py          # SQLAlchemy modely (Bucket, S3Object)
├── schemas.py         # Pydantic schémata (request/response)
├── database.py        # Připojení k databázi a session
├── alembic.ini        # Konfigurace Alembic
├── alembic/
│   ├── env.py         # Alembic environment
│   └── versions/      # Migrační skripty
└── requirements.txt   # Python závislosti
```

## Technologie

- [FastAPI](https://fastapi.tiangolo.com/) – webový framework
- [SQLAlchemy](https://www.sqlalchemy.org/) – ORM
- [Alembic](https://alembic.sqlalchemy.org/) – databázové migrace
- [Pydantic](https://docs.pydantic.dev/) – validace dat
- [Uvicorn](https://www.uvicorn.org/) – ASGI server
- SQLite – databáze
