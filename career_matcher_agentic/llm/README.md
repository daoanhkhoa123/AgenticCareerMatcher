# `career_matcher_agentic/llm`

Shared Gemini client, used by anything in the project that needs to call an
LLM directly (as opposed to being an MCP tool itself). Originally lived inside
`mcp_servers/career_matcher/` for CV parsing only; moved here once the
Streamlit host (`mcp_host/llm.py`) needed the same client for its chat loop —
"inside one MCP server's folder" was the wrong home for something two
independent parts of the app both depend on.

## Files

- **`key_config.py`** — `KeyConfig`, a `pydantic-settings` `BaseSettings`
  singleton that reads `GEMINI_API_KEY` from a local `.key` file
  (`llm/.key`, git-ignored; `llm/.key.example` shows the expected format).
  Validated once at import time — if the key is missing, importing this
  module raises immediately rather than failing later on first use.
- **`gemini_client.py`** — `get_gemini_client()`, a lazily-constructed
  `genai.Client` singleton built from `KeyConfig.gemini_api_key`. Everything
  in the project that talks to Gemini goes through this one client instance.

## Usage pattern

```python
from career_matcher_agentic.llm.gemini_client import get_gemini_client

client = get_gemini_client()
response = client.models.generate_content(model="gemini-3.6-flash", contents=...)
```

## Who uses this

- **`mcp_servers/career_matcher/cv_parsing.py`** — sends a CV (PDF as inline
  bytes, or plain text) to Gemini with a Pydantic `response_schema` to extract
  a structured skills list for `match_jobs_from_cv`.
- **`mcp_host/llm.py`** — the Streamlit host's tool-calling loop: builds a
  `types.Tool` from the connected MCP servers' tool listings and drives the
  "send message → maybe call a tool → feed result back → get final answer"
  loop against Gemini.

## Design notes

- **This package only owns the client, not the model name.** Both consumers
  above independently define their own `_MODEL = "gemini-3.6-flash"` constant
  rather than importing a shared one from here. That's a minor duplication
  worth knowing about if the model ever needs to change — right now it means
  updating it in two places, not one.
- **The `.key` file is intentionally separate from `.env`-style config.**
  Following the same pattern as `mcp_servers/crawler/` (`.key` for secrets,
  `.env` for non-secret settings like `max_listing_pages`), a secret gets its
  own file rather than being mixed into general configuration.
