"""Bridges MCP tool listings into Groq's OpenAI-compatible function-calling loop."""

import json
from typing import Any

from career_matcher_agentic.llm.groq_client import get_groq_client
from career_matcher_agentic.mcp_host.mcp_bridge import McpBridge, ToolInfo

_MODEL = "openai/gpt-oss-120b"
_SEP = "__"
_MAX_ROUNDS = 5

_SYSTEM_INSTRUCTION = (
    "You are a career-matching assistant backed by MCP tools. Job-matching tools return a "
    "dict with matches, total_jobs_in_db, last_crawled_at, and an optional note. When a note "
    "is present, always relay it to the user, mention how many jobs are in the database and "
    "when it was last crawled, and explicitly ask whether they'd like you to trigger a crawl "
    "(via the trigger_crawler tool) for fresher or more data - don't just report matches as if "
    "the dataset were complete and up to date.\n\n"
    "When the user wants to find or crawl jobs but hasn't given a URL, call list_supported_sites "
    "first and proactively suggest one of the listed sites (e.g. itviec.com) instead of just "
    "asking them to paste a URL - sites on that list have dedicated, higher-quality crawler "
    "support, while any other URL falls back to slower/costlier generic extraction.\n\n"
    "For CV-based matching, prefer match_jobs_from_cv_embedding over match_jobs_from_cv by default - "
    "it ranks jobs by semantic similarity, so it surfaces conceptually related roles that a literal "
    "tech-stack keyword overlap would miss. If its note reports very few or no matches, also try "
    "match_jobs_from_cv (keyword-based) as a fallback before telling the user nothing matches. Both "
    "CV tools need a real file_path on disk - if the user has uploaded a CV through the UI, its path "
    "will be given to you in the message context; use that exact path rather than asking the user to "
    "type one, unless no such path is present."
)


def _qualified_name(tool: ToolInfo) -> str:
    return f"{tool.server.replace('-', '_')}{_SEP}{tool.name}"


def _build_tools(tool_infos: list[ToolInfo]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": _qualified_name(tool),
                "description": tool.description,
                "parameters": tool.input_schema,
            },
        }
        for tool in tool_infos
    ]


def run_turn(
    history: list[dict[str, Any]],
    user_message: str,
    bridge: McpBridge,
) -> tuple[str, list[dict[str, Any]]]:
    """Runs one user turn to completion, driving any tool calls the model requests.

    Mutates `history` in place (appends the user message, any assistant/tool-result
    turns, and the final answer) so the caller can persist it across turns.
    Returns the final answer text and a log of tool calls made this turn.
    """
    tool_infos = bridge.list_tools()
    by_qualified_name = {_qualified_name(t): t for t in tool_infos}
    tools = _build_tools(tool_infos)

    history.append({"role": "user", "content": user_message})

    tool_calls_log: list[dict[str, Any]] = []
    client = get_groq_client()

    for _ in range(_MAX_ROUNDS):
        messages = [{"role": "system", "content": _SYSTEM_INSTRUCTION}] + history
        response = client.chat.completions.create(model=_MODEL, messages=messages, tools=tools)
        message = response.choices[0].message

        if not message.tool_calls:
            history.append({"role": "assistant", "content": message.content or ""})
            return message.content or "", tool_calls_log

        history.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {"id": call.id, "type": "function", "function": {"name": call.function.name, "arguments": call.function.arguments}}
                    for call in message.tool_calls
                ],
            }
        )

        for call in message.tool_calls:
            tool = by_qualified_name.get(call.function.name)
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}

            if tool is None:
                result: Any = {"error": f"Unknown tool '{call.function.name}'"}
            else:
                result = bridge.call_tool(tool.server, tool.name, arguments)

            tool_calls_log.append({"tool": call.function.name, "arguments": arguments, "result": result})

            payload = result if isinstance(result, dict) else {"result": result}
            history.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(payload)})

    return "Sorry, I couldn't finish that after several tool calls - please try rephrasing.", tool_calls_log
