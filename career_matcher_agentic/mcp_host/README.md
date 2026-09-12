# `career_matcher_agentic/mcp_host`

The MCP host: a Streamlit chat app with an embedded LLM (Groq) that connects
to all three MCP servers and runs the tool-calling loop. Contrast with
`mcp_clients/`, which calls one tool by hand with no LLM involved.

## Files

- `mcp_bridge.py` — `McpBridge`: keeps all three server subprocesses
  connected via a background asyncio loop (Streamlit reruns the script on
  every interaction, so connections can't be per-run). Exposes sync
  `list_tools()`/`call_tool()`.
- `llm.py` — `run_turn(history, user_message, bridge)`: converts MCP tools
  into OpenAI-style function schemas, calls Groq, dispatches any requested
  tool calls through the bridge (capped at 5 rounds), feeds results back.
- `app.py` — the Streamlit UI: chat box, CV upload, and an expandable panel
  per turn showing tool calls and results.

## Running it

```bash
uv run streamlit run career_matcher_agentic/mcp_host/app.py
```

## Notes

- Server subprocesses stay alive for the life of the Streamlit process.
- The model name (`openai/gpt-oss-120b`) is a local constant here too, same
  as in `llm/`.
