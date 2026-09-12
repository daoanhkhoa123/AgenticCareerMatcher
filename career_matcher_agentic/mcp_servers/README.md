# `career_matcher_agentic/mcp_servers`

Three MCP servers, each its own subpackage and process:

- `career_matcher/` — matches by exact skill overlap.
- `crawler/` — scrapes job boards into the database.
- `embedding_matcher/` — matches by semantic similarity.

See each subfolder's README for details.

## Why separate servers

Each groups one responsibility and one failure surface:

- `crawler` touches unpredictable external sites/APIs, so a flaky crawl
  can't take down matching.
- `career_matcher` and `embedding_matcher` are different matching
  strategies with different dependencies (DB-only vs. embedding API) —
  either can change or fail independently. The host decides which to try
  first and whether to fall back.
