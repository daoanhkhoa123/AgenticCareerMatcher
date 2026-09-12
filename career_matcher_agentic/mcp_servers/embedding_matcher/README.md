# `career_matcher_agentic/mcp_servers/embedding_matcher`

MCP server (`embedding-matcher-mcp`) implementing **semantic** CV-to-job
matching — the RAG half of the project. Its sibling `mcp_servers/career_matcher`
does exact skill-keyword overlap; this one ranks jobs by embedding distance,
so it can surface conceptually related roles a literal keyword search would
miss (different tech naming, adjacent skillsets).

## Files

- **`matching.py`** — `match_jobs_by_embedding(profile, preferences, limit)`:
  builds one query string from the parsed CV's `skills`, `projects`,
  `certifications`, `experience`, `education`, and `preferences` (plus any
  chat-typed `preferences`), embeds it with `JinaEmbedder(task="retrieval.query")`,
  then retrieves the nearest `Job` rows directly from Postgres with
  `Job.embedding.cosine_distance(query_vector)` — no separate vector
  database, no in-Python similarity loop. Rows with no `embedding` yet
  (never crawled/embedded) are excluded via `.filter(Job.embedding.is_not(None))`.
  Returns the same `total_jobs_in_db`/`last_crawled_at`/`note` shape as
  `career_matcher`'s matcher, via the same `db.stats` helpers.
- **`server.py`** — the `MCPServer("embedding-matcher")` instance, its one
  tool, and `main()`.

## Tool

- **`match_jobs_from_cv_embedding(file_path, preferences, limit)`** — parses
  the CV via the shared `career_matcher_agentic/cv_parsing.py` (the exact
  same `parse_cv`/`CVProfile` used by `career_matcher`'s `match_jobs_from_cv`),
  then ranks jobs by semantic similarity instead of keyword overlap.

## Running it

```bash
uv run embedding-matcher-mcp
# or: uv run python -m career_matcher_agentic.mcp_servers.embedding_matcher.server
```

## Design notes

- **The query embedding uses a different `task` than the passage embeddings
  it's compared against.** The crawler embeds job postings with
  `task="retrieval.passage"` (see `mcp_servers/crawler/README.md`); this
  server embeds the CV query with `task="retrieval.query"`. Jina's v3 model
  tunes these differently — using the same task for both would still
  produce a comparable vector space, just a worse-ranked one.
- **Retrieval is a single SQL query, not an application-level nearest-neighbor
  loop.** `cosine_distance` is a `pgvector` operator; ordering by it and
  `LIMIT`ing pushes the actual similarity search into Postgres.
- **This server has no fallback of its own.** If embeddings are missing or
  matches are poor, it's the *host*'s system instruction
  (`mcp_host/llm.py`) that knows to fall back to `career_matcher`'s
  keyword-based `match_jobs_from_cv` — this server just does one thing.
