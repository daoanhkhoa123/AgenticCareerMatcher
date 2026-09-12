# `career_matcher_agentic/embedder`

Turns text into vectors via the Jina Embeddings API. This is what feeds the
`jobs` table's `embedding` column (see `db/README.md`) and what the
embedding-based CV matcher embeds a query against — the shared building
block for the project's RAG-style semantic search, independent of both the
relational matching logic and the Groq LLM client.

## Files

- **`key_config.py`** — `KeyConfig`, a `pydantic-settings` singleton reading
  `JINA_API_KEY` (field `jina_key`) from a local `.key` file
  (`embedder/.key`, git-ignored) — same secrets-in-their-own-file pattern
  used by `llm/` and `mcp_servers/crawler/`.
- **`settings.py`** — `EmbedderSettings`, non-secret config from a local
  `.env` file: `jina_url` (default `https://api.jina.ai/v1/embeddings`),
  `jina_timeout_seconds` (default 30), and `embedding_dimensions` (default
  1024) — the last one is what sizes the `pgvector` column in
  `db/models.py`, so changing it here changes the schema, not just the
  request payload.
- **`jina_embedder.py`** — `JinaEmbedder`, a thin client over Jina's
  `/v1/embeddings` endpoint. `embed(texts, task=...)` batches any number of
  strings into one HTTP call and returns one vector per input, in order;
  `__call__(text)` is a single-string convenience wrapper around it.

## Usage pattern

```python
from career_matcher_agentic.embedder.jina_embedder import JinaEmbedder

embedder = JinaEmbedder()
vectors = embedder.embed(["Python, PyTorch, Docker"], task="retrieval.passage")
```

## Who uses this

- **`mcp_servers/crawler/crawling.py`** — batch-embeds every scraped posting
  (`title + company + requirements + tech_stack`) in one call with
  `task="retrieval.passage"`, storing the result in `Job.embedding` and the
  model name in `Job.embedding_model` on every upsert (new or updated).
- **`mcp_servers/embedding_matcher/matching.py`** — embeds a candidate's
  parsed CV as a single query with `task="retrieval.query"`, then retrieves
  the nearest `jobs` rows by cosine distance against those stored vectors.
- **`db/models.py`** — imports `EmbedderSettings.embedding_dimensions` to
  size the `embedding` column itself (`Vector(EmbedderSettings.embedding_dimensions)`).

## Design notes

- **`task=` isn't cosmetic.** Jina's v3 model produces task-tuned embeddings,
  so passages get embedded with `"retrieval.passage"` and the query side
  with `"retrieval.query"` — using the same task for both would still
  "work" (cosine distance is still computable) but retrieve worse matches,
  since the two task modes optimize the vector space differently for which
  side of a retrieval pair they represent.
- **Batching is deliberate on the crawler side.** One `embed(texts, ...)`
  call for all postings from a crawl, not one call per posting — fewer HTTP
  round-trips, and Jina's endpoint already accepts a list of inputs per call.
- **`embedding_dimensions` is a single source of truth.** It's read both when
  actually requesting embeddings from Jina (`jina_embedder.py`) and when
  declaring the database column's width (`db/models.py`) — changing it
  requires a new Alembic migration for the column, and re-embedding every
  existing row (a stale row's `embedding_model` is how you'd detect that a
  row hasn't been re-embedded at the new dimension yet).
