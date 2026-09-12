# `career_matcher_agentic/mcp_host`

A custom **MCP host**: a Streamlit chat app that embeds an LLM (Gemini),
connects to both MCP servers as a client, and runs the real
"chat message → model decides to call a tool → result comes back → final
answer" loop — the same role Claude Desktop or Claude Code plays, just with
Streamlit as the UI instead. Contrast with `mcp_clients/`, which calls one
tool by hand with no LLM involved.

## Files

- **`mcp_bridge.py`** — `McpBridge`, a persistent multi-server MCP connection
  manager. `mcp.Client` is async and meant to be entered once per connection,
  but Streamlit reruns the whole script synchronously on every interaction —
  re-spawning/re-handshaking both server subprocesses on every chat message
  would be slow. Instead, `McpBridge.__init__` starts a background thread
  running its own asyncio event loop, connects to both servers
  (`career-matcher-mcp`, `job-crawler-mcp`, launched as subprocesses via
  `StdioServerParameters`) on that loop, and keeps them open for the life of
  the process. `list_tools()`/`call_tool(...)` are plain sync methods that
  dispatch onto the background loop via `asyncio.run_coroutine_threadsafe`
  and block for the result — so the rest of the app never has to touch
  `async`/`await` at all.
- **`llm.py`** — `run_turn(history, user_message, bridge)`: the actual
  tool-calling loop. Converts every MCP tool from `bridge.list_tools()` into
  a Gemini `types.FunctionDeclaration` (passing `tool.input_schema` straight
  through as `parameters_json_schema` — Gemini accepts raw JSON Schema
  directly, no conversion needed), qualifies each tool's name as
  `server__toolname` so names stay unique across the two servers and a call
  can be routed back to the right one, then calls Gemini with the
  conversation history. While the model keeps requesting function calls
  (capped at 5 rounds), each one is dispatched through
  `bridge.call_tool(...)` and the result fed back as a `function_response`
  part — **`role="user"`**, not `"tool"`; Gemini's API rejects `"tool"` as an
  invalid role (only `USER`/`MODEL`/a few others are valid). Also carries
  `_SYSTEM_INSTRUCTION`, which tells the model to relay data-freshness
  caveats from job-matching tools and to proactively suggest a supported
  crawl target (via `list_supported_sites`) instead of just asking the user
  for a URL.
- **`app.py`** — the Streamlit script. `get_bridge()` is wrapped in
  `@st.cache_resource` so `McpBridge()` (and both server subprocesses) is
  created once per Streamlit process, not once per rerun. `st.session_state`
  holds two things across reruns: `history` (the Gemini `Content` list that
  `run_turn` mutates in place — this is the actual conversation context) and
  `messages` (a display-only log used to re-render past turns). Every turn
  shows an expandable panel listing any MCP tool calls made — name,
  arguments, result — so the plumbing is visible instead of hidden the way
  a production chat UI would hide it.

## Running it

```bash
uv run streamlit run career_matcher_agentic/mcp_host/app.py
```

## Design notes

- **Both server subprocesses stay running for the whole Streamlit process's
  life.** `McpBridge`'s background thread and its `Client` connections are
  never explicitly torn down; they die when the Streamlit process itself
  does. Fine for local/practice use, not something a production host would
  leave unmanaged.
- **`_call_tool` unwraps single-item results.** An MCP tool's `CallToolResult`
  can carry multiple content blocks; `mcp_bridge.py` JSON-decodes each block
  independently and returns a bare value if there's exactly one block, or a
  list if there's more than one — matching whatever shape the underlying
  Python tool function actually returned.
- **The model name (`gemini-3.6-flash`) is a local constant here too** — see
  the note in `llm/README.md` about it not being centralized in the shared
  Gemini client.
