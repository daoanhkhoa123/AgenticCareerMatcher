# `career_matcher_agentic/db`

Shared data-access layer for the whole project. Both MCP servers
(`mcp_servers/career_matcher`, `mcp_servers/crawler`) read and write the same
`jobs` table through this module — there is no separate database per server.

## Files

- **`base.py`** — `Base`, the SQLAlchemy `DeclarativeBase` every model inherits from.
- **`models.py`** — the `Job` ORM model (the only table right now) plus `Job.to_dict()`,
  used whenever a job needs to leave the DB layer as a plain JSON-serializable dict
  (MCP tool return values).
- **`session.py`** — `DATABASE_URL`, the `engine`, `SessionLocal` factory, and
  `get_session()`, a context manager that commits on success, rolls back on
  exception, and always closes the session.

## Schema — `jobs` table

| Column         | Type                     | Notes                                             |
|----------------|--------------------------|----------------------------------------------------|
| `id`           | int, PK                  |                                                    |
| `title`        | string(255)              |                                                    |
| `company`      | string(255)              |                                                    |
| `category`     | string(255)              | set by the crawler from the requested job category |
| `location`     | string(255), nullable    |                                                    |
| `remote`       | bool                     |                                                    |
| `url`          | string(2048), **unique** | identity key for crawler upserts (see below)      |
| `requirements` | text, nullable           | free-text requirements/qualifications             |
| `tech_stack`   | `ARRAY(String)`          | list of skills; matching does a set-overlap on this |
| `created_at`   | timestamptz              | server-set on insert                              |
| `updated_at`   | timestamptz              | server-set on insert, bumped on every update       |

Design choices worth knowing:
- **`tech_stack` is a native Postgres array, not JSON.** Matching only ever needs
  set-overlap against a list of skill strings, so an array keeps that simple with
  no JSON parsing/casting in either Python or SQL.
- **`url` is unique on purpose.** The crawler (`mcp_servers/crawler/crawling.py`,
  `_persist`) looks up a job by `url` and either updates the existing row or
  inserts a new one — this is what makes re-crawling the same listing an update
  instead of a duplicate.
- **`updated_at` doubles as a "last crawled at" signal.** Since it's bumped by
  `onupdate=func.now()` on every crawler upsert, `MAX(updated_at)` across the
  table (used in `mcp_servers/career_matcher/matching.py`) tells the assistant
  when the data was last refreshed, without needing a separate crawl-log table.

## How it connects to Postgres

Postgres runs via Docker Compose: the root `docker-compose.yml` just `include:`s
`third_party/postgre_sql/compose.job_db.yml`, which defines the actual service
(container `job_db`, database `job_db_postgre`, host port `5438`). `session.py`'s
`DATABASE_URL` default points at exactly that, and can be overridden with a
`DATABASE_URL` environment variable for a different environment.

## Migrations

Schema changes go through Alembic (configured at the repo root: `alembic.ini`,
`alembic/`). `alembic/env.py` imports `Base.metadata` and `DATABASE_URL` from
this package, so migrations are always generated/applied against the same
models and the same database as the app itself:

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

## Usage pattern

```python
from career_matcher_agentic.db.models import Job
from career_matcher_agentic.db.session import get_session

with get_session() as session:
    jobs = session.query(Job).all()
```

## Who uses this

- **`mcp_servers/career_matcher/matching.py`** — reads `jobs` to rank matches
  for `match_jobs_from_prompt`/`match_jobs_from_cv`, plus dataset stats
  (`total_jobs_in_db`, `last_crawled_at`) surfaced alongside the results.
- **`mcp_servers/crawler/crawling.py`** — upserts `Job` rows by `url` after a crawl.
