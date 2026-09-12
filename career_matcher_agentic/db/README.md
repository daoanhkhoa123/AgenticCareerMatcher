# `career_matcher_agentic/db`

Shared data-access layer for the whole project. All three MCP servers
(`mcp_servers/career_matcher`, `mcp_servers/crawler`,
`mcp_servers/embedding_matcher`) read and write the same `jobs` table through
this module — there is no separate database per server.

This is also the project's **vector database**, not just a relational one.
Since the `embedding` column below is a real `pgvector` column, Postgres
doubles as the retrieval store for RAG-style semantic search: a CV gets
embedded into the same vector space as every job posting, and the closest
postings by cosine distance are retrieved directly with SQL — no separate
vector DB (Pinecone, Chroma, etc.) needed.

## Files

- **`base.py`** — `Base`, the SQLAlchemy `DeclarativeBase` every model inherits from.
- **`models.py`** — the `Job` ORM model (the only table right now) plus `Job.to_dict()`,
  used whenever a job needs to leave the DB layer as a plain JSON-serializable dict
  (MCP tool return values). Imports `EmbedderSettings` from
  `career_matcher_agentic/embedder` to size the `embedding` column, so this module
  now transitively depends on that package.
- **`session.py`** — `DATABASE_URL`, the `engine`, `SessionLocal` factory, and
  `get_session()`, a context manager that commits on success, rolls back on
  exception, and always closes the session.

## Schema — `jobs` table

| Column            | Type                     | Notes                                                     |
|-------------------|--------------------------|------------------------------------------------------------|
| `id`              | int, PK                  |                                                            |
| `title`           | string(255)              |                                                            |
| `company`         | string(255)              |                                                            |
| `category`        | string(255)              | set by the crawler from the requested job category         |
| `location`        | string(255), nullable    |                                                            |
| `remote`          | bool                     |                                                            |
| `url`              | string(2048), **unique** | identity key for crawler upserts (see below)               |
| `requirements`    | text, nullable           | free-text requirements/qualifications                      |
| `tech_stack`      | `ARRAY(String)`          | list of skills; matching does a set-overlap on this         |
| `embedding`       | `vector(1024)`, nullable | Jina embedding of title+company+requirements+tech_stack    |
| `embedding_model` | string(255), nullable    | name of the model that produced `embedding` (e.g. `jina-embeddings-v3`) |
| `created_at`      | timestamptz              | server-set on insert                                        |
| `updated_at`      | timestamptz              | server-set on insert, bumped on every update                |

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
- **`embedding` is a real pgvector column, not JSON/array — this is what makes
  RAG-style retrieval possible.** The Postgres `vector` extension is enabled
  via migration (`13f7bae29325`), and `models.py` declares the column as
  `Vector(EmbedderSettings.embedding_dimensions)` from the `pgvector` package.
  The crawler (`mcp_servers/crawler/crawling.py`) computes it via
  `JinaEmbedder` from `title + company + requirements + tech_stack` and
  re-embeds on every upsert (new or updated), so it always reflects the row's
  current content. At query time, `mcp_servers/embedding_matcher/matching.py`
  embeds the candidate's CV into the same vector space and retrieves the
  nearest job postings straight from Postgres with
  `Job.embedding.cosine_distance(query_vector)` — semantic retrieval with no
  separate vector store. `embedding_model` records which model produced the
  vector, so a future change of embedding model/dimensions is detectable
  per-row instead of silently mixing incompatible vectors.

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
  for `match_jobs_from_prompt`/`match_jobs_from_cv` by exact skill-keyword
  overlap, plus dataset stats (`total_jobs_in_db`, `last_crawled_at`)
  surfaced alongside the results.
- **`mcp_servers/embedding_matcher/matching.py`** — the RAG path:
  `match_jobs_from_cv_embedding` embeds the parsed CV and retrieves the
  nearest `jobs` rows by `embedding` (cosine distance), surfacing
  conceptually related roles a keyword search would miss.
- **`mcp_servers/crawler/crawling.py`** — upserts `Job` rows by `url` after a crawl,
  including a batch-computed `embedding`/`embedding_model` per posting via
  `career_matcher_agentic/embedder/jina_embedder.py` — this is what populates
  the vector store that the embedding matcher retrieves from.
