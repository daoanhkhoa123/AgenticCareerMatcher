"""Bridges MCP tool listings into Gemini's manual function-calling loop."""

from typing import Any

from google.genai import types

from career_matcher_agentic.mcp_host.mcp_bridge import McpBridge, ToolInfo
from career_matcher_agentic.llm.gemini_client import get_gemini_client

_MODEL = "gemini-3.6-flash"
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
    "support, while any other URL falls back to slower/costlier generic extraction."
)


def _qualified_name(tool: ToolInfo) -> str:
    return f"{tool.server.replace('-', '_')}{_SEP}{tool.name}"


def _build_tool(tool_infos: list[ToolInfo]) -> types.Tool:
    declarations = [
        types.FunctionDeclaration(
            name=_qualified_name(tool),
            description=tool.description,
            parameters_json_schema=tool.input_schema,
        )
        for tool in tool_infos
    ]
    return types.Tool(function_declarations=declarations)


def run_turn(
    history: list[types.Content],
    user_message: str,
    bridge: McpBridge,
) -> tuple[str, list[dict[str, Any]]]:
    """Runs one user turn to completion, driving any tool calls the model requests.

    Mutates `history` in place (appends the user message, any model/tool-result
    turns, and the final answer) so the caller can persist it across turns.
    Returns the final answer text and a log of tool calls made this turn.
    """
    tool_infos = bridge.list_tools()
    by_qualified_name = {_qualified_name(t): t for t in tool_infos}
    gemini_tool = _build_tool(tool_infos)
    config = types.GenerateContentConfig(tools=[gemini_tool], system_instruction=_SYSTEM_INSTRUCTION)

    history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

    tool_calls_log: list[dict[str, Any]] = []
    client = get_gemini_client()

    for _ in range(_MAX_ROUNDS):
        response = client.models.generate_content(model=_MODEL, contents=history, config=config)
        history.append(response.candidates[0].content)

        function_calls = response.function_calls
        if not function_calls:
            return response.text or "", tool_calls_log

        response_parts = []
        for call in function_calls:
            tool = by_qualified_name.get(call.name)
            arguments = dict(call.args or {})

            if tool is None:
                result: Any = {"error": f"Unknown tool '{call.name}'"}
            else:
                result = bridge.call_tool(tool.server, tool.name, arguments)

            tool_calls_log.append({"tool": call.name, "arguments": arguments, "result": result})

            response_payload = result if isinstance(result, dict) else {"result": result}
            response_parts.append(types.Part.from_function_response(name=call.name, response=response_payload))

        history.append(types.Content(role="user", parts=response_parts))

    return "Sorry, I couldn't finish that after several tool calls - please try rephrasing.", tool_calls_log
