# `career_matcher_agentic/mcp_servers/career_matcher`

MCP server for keyword/skill-overlap job matching. Its sibling
`embedding_matcher` does the same job by semantic similarity instead.

## Files

- `matching.py` — `match_jobs(skills, preferences, limit)`: scores jobs by
  overlap between `skills` and `job.tech_stack`, filters to remote jobs if
  requested, returns top matches plus `total_jobs_in_db`/`last_crawled_at`/`note`.
- `server.py` — the `MCPServer("career-matcher")` instance and tools.

## Tools

- `match_jobs_from_prompt(skills, preferences, limit)` — skills typed in chat.
- `match_jobs_from_cv(file_path, preferences, limit)` — extracts skills
  from a CV via `cv_parsing.py`, then matches.

Both return:
```python
{"matches": [...], "total_jobs_in_db": int, "last_crawled_at": str | None, "note": str | None}
```

## Running it

```bash
uv run career-matcher-mcp
```

## Notes

Matching is exact, case-insensitive set-overlap — no fuzziness.
`embedding_matcher` exists to catch conceptually related matches this misses.
