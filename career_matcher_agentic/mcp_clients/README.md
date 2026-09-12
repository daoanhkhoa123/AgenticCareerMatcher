# `career_matcher_agentic/mcp_clients`

A minimal, **manual** MCP client — no LLM involved. It exists to show the raw
client side of the MCP protocol by hand: connect, `initialize`, `list_tools`,
`call_tool`, done. Useful for learning/debugging a server directly, without
needing a full chat app in the loop.

This is a different thing from `mcp_host/`: `mcp_host` is a real **host** — it
embeds an LLM (Groq) that *decides* which tool to call based on a chat
message. This package skips that decision entirely and just calls a specific
tool with hardcoded arguments, so you can see exactly what a client does
without also reasoning about model behavior.

## Files

- **`career_matcher_client.py`** — connects to `career-matcher-mcp` over
  stdio (spawns it as a subprocess via `StdioServerParameters`), prints every
  tool the server exposes (name + description), then calls
  `match_jobs_from_prompt` with hardcoded skills and pretty-prints the result.

## Running it

```bash
uv run python career_matcher_agentic/mcp_clients/career_matcher_client.py
```

## Design notes

- **Only talks to one server** (`career-matcher-mcp`), and only calls one
  tool with fixed arguments. It's a demonstration script, not a general
  MCP debugging tool — extend it (or copy the pattern into a new script) if
  you want to poke at `job-crawler-mcp`, `embedding-matcher-mcp`, or a
  different tool the same way. The project now has three MCP servers total
  (`mcp_host/mcp_bridge.py` connects to all of them); this client only ever
  demonstrates one at a time.
- **The tool call's arguments are hardcoded**, not user input — this is
  intentionally the simplest possible example of `list_tools` + `call_tool`,
  not a reusable CLI.
- **Whatever the tool returns is just printed as-is.** `match_jobs_from_prompt`
  currently returns `{"matches": [...], "total_jobs_in_db": ..., "last_crawled_at": ...,
  "note": ...}` (see `mcp_servers/career_matcher/matching.py`), but this script
  doesn't assume that shape — it just JSON-pretty-prints whatever comes back,
  so it keeps working if the tool's return shape changes.
