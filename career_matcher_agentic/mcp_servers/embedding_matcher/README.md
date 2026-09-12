# `career_matcher_agentic/mcp_servers/embedding_matcher`

MCP server (`embedding-matcher-mcp`) for semantic CV-to-job matching — the
RAG half of the project. Ranks jobs by embedding distance instead of
keyword overlap.

## Files

- `matching.py` — `match_jobs_by_embedding(profile, preferences, limit)`:
  builds a query string from the parsed CV, embeds it
  (`task="retrieval.query"`), and retrieves the nearest `Job` rows by
  `cosine_distance` directly in Postgres.
- `server.py` — the `MCPServer("embedding-matcher")` instance and tool.

## Tool

- `match_jobs_from_cv_embedding(file_path, preferences, limit)`

## Running it

```bash
uv run embedding-matcher-mcp
```

## Notes

No fallback of its own — the host (`mcp_host/llm.py`) falls back to
`career_matcher`'s keyword matching if this returns too little.
