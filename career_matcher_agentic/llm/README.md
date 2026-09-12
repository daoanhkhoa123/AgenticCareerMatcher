# `career_matcher_agentic/llm`

Shared Groq client, used by anything in the project that needs to call an
LLM directly (as opposed to being an MCP tool itself). Originally wrapped
Gemini; migrated to Groq's OpenAI-compatible chat completions API once
Gemini's quota became a blocker for local development.

## Files

- **`key_config.py`** — `KeyConfig`, a `pydantic-settings` `BaseSettings`
  singleton that reads `GROQ_API_KEY` from a local `.key` file
  (`llm/.key`, git-ignored). Validated once at import time — if the key is
  missing, importing this module raises immediately rather than failing
  later on first use.
- **`groq_client.py`** — `get_groq_client()`, a lazily-constructed `Groq`
  client singleton built from `KeyConfig.groq_api_key`. Everything in the
  project that talks to an LLM goes through this one client instance.

## Usage pattern

```python
from career_matcher_agentic.llm.groq_client import get_groq_client

client = get_groq_client()
response = client.chat.completions.create(model="openai/gpt-oss-120b", messages=[...])
```

## Who uses this

- **`cv_parsing.py`** — extracts CV text itself (via `pypdf` for `.pdf`, plain
  decoding for everything else — Groq's chat models don't accept a raw PDF
  file the way Gemini's `Part.from_bytes` did), then asks the model for a
  JSON object (`response_format={"type": "json_object"}`) matching the
  `CVProfile` shape (skills, projects, certifications, preferences,
  experience, education) used by both `match_jobs_from_cv` and
  `match_jobs_from_cv_embedding`.
- **`mcp_host/llm.py`** — the Streamlit host's tool-calling loop: builds
  OpenAI-style `tools` from the connected MCP servers' tool listings and
  drives the "send message → maybe call a tool → feed result back → get
  final answer" loop against Groq.

## Design notes

- **This package only owns the client, not the model name.** Both consumers
  above independently define their own `_MODEL = "openai/gpt-oss-120b"`
  constant rather than importing a shared one from here. That's a minor
  duplication worth knowing about if the model ever needs to change — right
  now it means updating it in two places, not one.
- **The `.key` file is intentionally separate from `.env`-style config.**
  Following the same pattern as `mcp_servers/crawler/` (`.key` for secrets,
  `.env` for non-secret settings like `max_listing_pages`), a secret gets its
  own file rather than being mixed into general configuration.
- **`history`/message format is now plain OpenAI-style dicts**
  (`{"role": ..., "content": ...}`, with `tool_calls`/`tool_call_id` on the
  relevant turns), not the Gemini SDK's `types.Content` objects. `mcp_host/app.py`
  just holds `history` opaquely in `st.session_state` and never constructs
  message objects itself, so this only affected `llm.py` internally.
