# `career_matcher_agentic/mcp_host`

A custom **MCP host**: a Streamlit chat app that embeds an LLM (Groq),
connects to all three MCP servers as a client, and runs the real
"chat message → model decides to call a tool → result comes back → final
answer" loop — the same role Claude Desktop or Claude Code plays, just with
Streamlit as the UI instead. Contrast with `mcp_clients/`, which calls one
tool by hand with no LLM involved.

## Files

- **`mcp_bridge.py`** — `McpBridge`, a persistent multi-server MCP connection
  manager. `mcp.Client` is async and meant to be entered once per connection,
  but Streamlit reruns the whole script synchronously on every interaction —
  re-spawning/re-handshaking all server subprocesses on every chat message
  would be slow. Instead, `McpBridge.__init__` starts a background thread
  running its own asyncio event loop, connects to every server listed in
  `_SERVERS` (`career-matcher-mcp`, `job-crawler-mcp`, `embedding-matcher-mcp`,
  each launched as a subprocess via `StdioServerParameters`) on that loop, and
  keeps them open for the life of the process. `list_tools()`/`call_tool(...)`
  are plain sync methods that dispatch onto the background loop via
  `asyncio.run_coroutine_threadsafe` and block for the result — so the rest of
  the app never has to touch `async`/`await` at all.
- **`llm.py`** — `run_turn(history, user_message, bridge)`: the actual
  tool-calling loop. Converts every MCP tool from `bridge.list_tools()` into
  an OpenAI-style `tools` entry (passing `tool.input_schema` straight through
  as the function's `parameters` — Groq accepts raw JSON Schema directly, no
  conversion needed), qualifies each tool's name as `server__toolname` so
  names stay unique across servers and a call can be routed back to the
  right one, then calls Groq with the conversation history (a plain list of
  OpenAI-style message dicts). While the model keeps requesting function
  calls (capped at 5 rounds), each one is dispatched through
  `bridge.call_tool(...)` and the result fed back as a `{"role": "tool", ...}`
  message. Also carries `_SYSTEM_INSTRUCTION`, which tells the model to relay
  data-freshness
  caveats from job-matching tools, to proactively suggest a supported
  crawl target (via `list_supported_sites`) instead of just asking the user
  for a URL, and to prefer the embedding-based CV matcher over the keyword one
  (falling back to keyword matching if embedding matching finds too little),
  using whatever uploaded-CV path `app.py` puts in the message context.
- **`app.py`** — the Streamlit script. `get_bridge()` is wrapped in
  `@st.cache_resource` so `McpBridge()` (and all server subprocesses) is
  created once per Streamlit process, not once per rerun. A sidebar
  `st.file_uploader` accepts a `.pdf` or `.txt` CV, writes it into a
  session-scoped temp directory, and stores the resulting path in
  `st.session_state.cv_path`; whenever a path is present, it's prepended as
  context to the next chat message sent to `run_turn` (the chat bubble itself
  still shows the user's original text) so the model can pass it straight
  through as `file_path` to a CV tool instead of the user having to type one.
  `st.session_state` also holds `history` (the OpenAI-style message dict list
  that `run_turn` mutates in place — this is the actual conversation context) and
  `messages` (a display-only log used to re-render past turns). Every turn
  shows an expandable panel listing any MCP tool calls made — name,
  arguments, result — so the plumbing is visible instead of hidden the way
  a production chat UI would hide it.

## Running it

```bash
uv run streamlit run career_matcher_agentic/mcp_host/app.py
```

## Design notes

- **All three server subprocesses stay running for the whole Streamlit
  process's life.** `McpBridge`'s background thread and its `Client`
  connections are never explicitly torn down; they die when the Streamlit
  process itself does. Fine for local/practice use, not something a
  production host would leave unmanaged.
- **The system instruction is resent every round, not sent once.** `llm.py`
  prepends `{"role": "system", "content": _SYSTEM_INSTRUCTION}` to `history`
  fresh on every iteration of the tool-calling loop, rather than storing it
  in `history` itself — simpler than tracking whether it's already present,
  at the cost of resending those tokens on every round-trip.
- **`_call_tool` unwraps single-item results.** An MCP tool's `CallToolResult`
  can carry multiple content blocks; `mcp_bridge.py` JSON-decodes each block
  independently and returns a bare value if there's exactly one block, or a
  list if there's more than one — matching whatever shape the underlying
  Python tool function actually returned.
- **The model name (`openai/gpt-oss-120b`) is a local constant here too** —
  see the note in `llm/README.md` about it not being centralized in the
  shared Groq client.
