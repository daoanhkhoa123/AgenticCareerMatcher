# `career_matcher_agentic/db`

Shared data-access layer. All three MCP servers read/write the same `jobs`
table, which also doubles as the vector store (`pgvector`) for semantic
search — no separate vector DB.

## Files

- `base.py` — `Base`, the SQLAlchemy declarative base.
- `models.py` — the `Job` ORM model + `Job.to_dict()`.
- `session.py` — `DATABASE_URL`, `engine`, `SessionLocal`, `get_session()`.

## Schema — `jobs`

| Column            | Type                     | Notes                              |
|-------------------|--------------------------|-------------------------------------|
| `id`              | int, PK                  |                                      |
| `title`           | string(255)              |                                      |
| `company`         | string(255)              |                                      |
| `category`        | string(255)              | set by the crawler                  |
| `location`        | string(255), nullable    |                                      |
| `remote`          | bool                     |                                      |
| `url`             | string(2048), unique     | crawler upsert key                  |
| `requirements`    | text, nullable           |                                      |
| `tech_stack`      | `ARRAY(String)`          | matched via set-overlap             |
| `embedding`       | `vector(1024)`, nullable | Jina embedding of the posting       |
| `embedding_model` | string(255), nullable    | e.g. `jina-embeddings-v3`           |
| `created_at`      | timestamptz              |                                      |
| `updated_at`      | timestamptz              | doubles as "last crawled at"        |

## Postgres

Runs via Docker Compose (`third_party/postgre_sql/compose.job_db.yml`,
included from the root `docker-compose.yml`). `DATABASE_URL` can be
overridden with an env var.

## Migrations

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

## Usage

```python
from career_matcher_agentic.db.models import Job
from career_matcher_agentic.db.session import get_session

with get_session() as session:
    jobs = session.query(Job).all()
```
