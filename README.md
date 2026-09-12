# Career Matcher Agentic

A practice project for building a real, working **MCP (Model Context
Protocol)** system end-to-end — not just a server, but the whole picture:
multiple MCP servers exposing tools, a minimal hand-written client, and a
custom chat **host** (Streamlit + Gemini) that drives the actual
tool-calling loop, instead of relying on Claude Desktop/Code as the host.

The domain happens to be a career-matching assistant: it can search a local
job database, crawl real job boards to populate it, and match a candidate's
skills — typed manually or extracted from an uploaded CV — against real
postings.

## Demo

The chat is transparent about the underlying MCP tool calls and honest about
data quality — it won't silently report matches against an empty or stale
database.

**No jobs yet — the assistant reports it plainly and proactively suggests a
supported crawl target instead of asking for a URL blindly:**

![Assistant finds no jobs in the database and asks whether to crawl a predefined, supported site](docs/ai_found_no_jobs_in_db_and_asking_if_wanted_to_crawl_predefined_website.png)

**After confirming, the crawl runs and the same request now returns real,
ranked matches:**

![Assistant reports a successful crawl and returns ranked job matches](docs/ai_returning_jobs_after_finishing_crawling.png)

**The same reply also states the database's new size and last-crawled time:**

![Assistant showing total jobs in the database and the last-crawled timestamp after crawling](docs/ai_showing_database_status_after_crawling.png)

## Architecture overview

![Architecture diagram](docs/architecture.svg)

- A **Streamlit app is the MCP host** (`career_matcher_agentic/mcp_host/`) —
  what the user actually opens in a browser. It embeds a Gemini LLM and a
  persistent MCP client connected to both servers, and runs the full loop:
  user message → model decides whether to call a tool → the call is
  dispatched to the right server → the result is fed back → final answer.
- Two **MCP servers** expose the actual capabilities as tools (see below).
- A minimal **MCP client** (`mcp_clients/`) exists separately from the host,
  purely to call one tool by hand with no LLM involved — useful for seeing
  the raw protocol mechanics (`initialize` → `list_tools` → `call_tool`)
  without also reasoning about model behavior.
- **Gemini** (`llm/`, via the `google-genai` SDK) is the one LLM used
  everywhere — driving the host's chat loop, and doing structured CV-skill
  extraction.
- **PostgreSQL** (`third_party/postgre_sql/`, run via Docker Compose) is the
  single shared datastore — both MCP servers read and write the same `jobs`
  table.

## MCP servers and their tools

- **`career-matcher-mcp`** (`mcp_servers/career_matcher/`)
  - `match_jobs_from_prompt` — rank jobs against skills/preferences typed
    directly in chat.
  - `match_jobs_from_cv` — extract skills from an uploaded CV (PDF or text,
    via Gemini) and rank jobs the same way.
  - Both return match count, total jobs in the database, when the data was
    last crawled, and a caveat when the result looks sparse/stale.
- **`job-crawler-mcp`** (`mcp_servers/crawler/`)
  - `trigger_crawler` — scrape a job board URL for a category and
    upsert the postings into the database.
  - `list_supported_sites` — which sites have a dedicated, higher-quality
    crawler (currently itviec.com) versus falling back to generic
    Firecrawl-based LLM extraction for anything else.

Each subpackage under `career_matcher_agentic/` has its own `README.md` with
the actual design details — this file is the map, not the territory.

## MCP client vs. MCP host

These get confused easily, so to be explicit: a **client** just speaks the
protocol (`list_tools`, `call_tool`) — it can be driven by a human calling a
specific tool on purpose (`mcp_clients/`), or embedded inside a **host** that
also has an LLM deciding *which* tool to call and *when*, based on a chat
message (`mcp_host/`). Both talk to the exact same servers; only the host has
a model in the loop.

## LLM: Gemini

All LLM calls in this project — the host's chat/tool-calling loop and CV
skill extraction — go through one shared client in `career_matcher_agentic/llm/`,
built on the `google-genai` SDK. Structured extraction (CV → skills list) uses
Gemini's Pydantic `response_schema` support; the host's tool-calling loop uses
manual function calling, passing each MCP tool's JSON Schema straight through
to Gemini with no conversion layer.

## Frontend: Streamlit as the MCP host

`career_matcher_agentic/mcp_host/app.py` is the actual UI — a chat box, with
an expandable panel on every turn showing exactly which MCP tool(s) got
called, with what arguments, and what came back. That transparency is
deliberate: the point of this project is to see MCP working, not to hide it
behind a polished assistant.

## Database: PostgreSQL

A single `jobs` table, shared by both MCP servers, running in Docker
(`third_party/postgre_sql/compose.job_db.yml`, included from the root
`docker-compose.yml`). Schema managed with Alembic. See
`career_matcher_agentic/db/README.md` for the schema and design notes.

## Project layout

```text
career_matcher_agentic/
├── db/            shared SQLAlchemy models + session (the jobs table)
├── llm/           shared Gemini client + API key config
├── mcp_servers/
│   ├── career_matcher/   MCP server: match_jobs_from_prompt, match_jobs_from_cv
│   └── crawler/          MCP server: trigger_crawler, list_supported_sites
├── mcp_clients/   manual MCP client (no LLM) — protocol demo
├── mcp_host/      Streamlit chat app — the real MCP host (LLM + MCP client)
└── logging/       shared logging setup (writes to app.log at the repo root)
third_party/
└── postgre_sql/   Docker Compose service definition for Postgres
```

## Running it

```bash
# 1. Start Postgres
docker compose up -d

# 2. Apply migrations
uv run alembic upgrade head

# 3. Launch the chat app (spawns both MCP servers itself)
uv run streamlit run career_matcher_agentic/mcp_host/app.py
```

Requires a `GEMINI_API_KEY` in `career_matcher_agentic/llm/.key` and a
`FIRECRAWL_API_KEY` in `career_matcher_agentic/mcp_servers/crawler/.key`
(see the `.key.example` files next to each).
