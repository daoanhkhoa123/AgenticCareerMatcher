"""Keeps one persistent MCP Client per configured server alive on a
background asyncio event loop, so a synchronous caller (Streamlit) never
pays the cost of re-spawning/re-handshaking a server subprocess per call."""

import asyncio
import json
import threading
from concurrent.futures import Future
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters

_PROJECT_ROOT = Path(__file__).parent.parent.parent

_SERVERS: dict[str, StdioServerParameters] = {
    "career-matcher": StdioServerParameters(
        command="uv", args=["run", "career-matcher-mcp"], cwd=str(_PROJECT_ROOT)
    ),
    "job-crawler": StdioServerParameters(
        command="uv", args=["run", "job-crawler-mcp"], cwd=str(_PROJECT_ROOT)
    ),
}


@dataclass
class ToolInfo:
    server: str
    name: str
    description: str
    input_schema: dict[str, Any]


class McpBridge:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._clients: dict[str, Client] = {}
        self._tools: list[ToolInfo] = []

        ready: Future[None] = Future()
        self._thread = threading.Thread(target=self._run_loop, args=(ready,), daemon=True)
        self._thread.start()
        ready.result()

    def _run_loop(self, ready: Future[None]) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_all())
        except Exception as exc:
            ready.set_exception(exc)
            return
        ready.set_result(None)
        self._loop.run_forever()

    async def _connect_all(self) -> None:
        for name, params in _SERVERS.items():
            client = Client(params)
            await client.__aenter__()
            self._clients[name] = client

            listed = await client.list_tools()
            for tool in listed.tools:
                self._tools.append(
                    ToolInfo(
                        server=name,
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.input_schema,
                    )
                )

    def list_tools(self) -> list[ToolInfo]:
        return list(self._tools)

    def call_tool(self, server: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        future = asyncio.run_coroutine_threadsafe(self._call_tool(server, tool_name, arguments), self._loop)
        return future.result()

    async def _call_tool(self, server: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        client = self._clients[server]
        result = await client.call_tool(tool_name, arguments)

        parsed: list[Any] = []
        for block in result.content:
            if not hasattr(block, "text"):
                continue
            try:
                parsed.append(json.loads(block.text))
            except (json.JSONDecodeError, ValueError):
                parsed.append(block.text)

        if len(parsed) == 1:
            return parsed[0]
        return parsed
