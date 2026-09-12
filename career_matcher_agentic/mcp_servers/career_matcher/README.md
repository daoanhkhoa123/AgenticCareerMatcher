# `career_matcher_agentic/mcp_servers/career_matcher`

MCP server exposing **keyword/skill-overlap** job matching. Its sibling
`mcp_servers/embedding_matcher` does the same job conceptually
(CV → ranked matches) but by semantic similarity instead — this server is
the literal, exact-match half of that pair.

## Files

- **`matching.py`** — `match_jobs(skills, preferences, limit)`: normalizes
  `skills` to lowercase, scores each `Job` row by the size of the overlap
  between that set and `job.tech_stack`, filters to `remote=True` rows if
  `"remote"` appears in `preferences`, and returns the top `limit` by score.
  Also pulls `total_jobs_in_db`/`last_crawled_at` via
  `career_matcher_agentic.db.stats.get_dataset_stats` and a `note` via
  `build_staleness_note` — see `db/README.md` for what those mean.
- **`server.py`** — the `MCPServer("career-matcher")` instance and its two
  tools, plus `main()`.

## Tools

- **`match_jobs_from_prompt(skills, preferences, limit)`** — skills typed
  directly in chat.
- **`match_jobs_from_cv(file_path, preferences, limit)`** — calls
  `parse_cv()` (shared top-level `career_matcher_agentic/cv_parsing.py`, not
  local to this package — `mcp_servers/embedding_matcher` imports the exact
  same function) to get a `CVProfile.skills` list, then calls `match_jobs`
  with those.

Both return the same shape:
```python
{"matches": [...], "total_jobs_in_db": int, "last_crawled_at": str | None, "note": str | None}
```

## Running it

```bash
uv run career-matcher-mcp
# or: uv run python -m career_matcher_agentic.mcp_servers.career_matcher.server
```

## Design notes

- **Matching is exact set-overlap, not semantic.** `"PyTorch"` matches
  `"pytorch"` (case-insensitive) but not `"Torch"` or `"Deep Learning
  frameworks"` — there's no fuzziness here on purpose. `embedding_matcher`
  exists specifically to catch the conceptually-related matches this server
  misses; the host's system instruction (`mcp_host/llm.py`) tells the model
  to prefer the embedding matcher for CVs and fall back to this one.
- **`cv_parsing.py` isn't local to this package anymore.** It used to live
  here; it moved to the top level of `career_matcher_agentic/` once
  `embedding_matcher` needed the exact same CV-extraction logic — two
  independent servers depending on "the career_matcher server's internals"
  was the wrong shape.
