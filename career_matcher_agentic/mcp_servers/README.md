# `career_matcher_agentic/mcp_servers`

Every MCP server in the project lives here, each as its own subpackage and
its own separately-runnable process:

- **`career_matcher/`** — matches a candidate to jobs by exact skill overlap.
- **`crawler/`** — scrapes job board listings into the shared database.
- **`embedding_matcher/`** — matches a candidate to jobs by semantic
  similarity instead of exact overlap.

Each has its own `README.md` with the actual tools and implementation
details — this file only answers "why so many servers instead of one?"

## Why split across servers at all

A single MCP server exposing every tool would work — MCP doesn't require
this split. It's done here because each server groups tools around one
coherent responsibility and one dependency/failure surface, so they can be
run, reasoned about, and fail independently:

- **`crawler` is separate because scraping is a fundamentally different kind
  of operation than the other two.** It reaches out to arbitrary,
  unpredictable external websites (plus the Firecrawl API), which is far
  more likely to be slow or fail than a local database query. Keeping it in
  its own process means a flaky crawl can't take down job matching.
- **`career_matcher` and `embedding_matcher` are separate because they're two
  different matching *strategies* with different dependencies**, not one
  feature with an option flag. Exact keyword matching only ever touches the
  database; semantic matching also depends on an embedding API. Splitting
  them means either one can change, fail, or be swapped out without
  touching the other — and it's the chat host, not either server, that
  decides which one to try first and whether to fall back to the other.

The tradeoff is real: more processes to run, and the host (`mcp_host/`) has
to manage connections to all of them instead of one. For a project whose
point is learning how MCP tool boundaries work in practice, that tradeoff is
the whole point, not a cost to avoid.
