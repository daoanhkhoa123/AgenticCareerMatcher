"""Minimal manual MCP client: connects to the career-matcher server over
stdio, lists its tools, and calls match_jobs_from_prompt directly (no LLM
involved) - useful for seeing the client side of the protocol by hand."""

import asyncio
import json
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters

_PROJECT_ROOT = Path(__file__).parent.parent.parent

_SERVER = StdioServerParameters(
    command="uv",
    args=["run", "career-matcher-mcp"],
    cwd=str(_PROJECT_ROOT),
)


async def main() -> None:
    async with Client(_SERVER) as client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description}")

        print("\nCalling match_jobs_from_prompt(skills=['Python', 'PyTorch'])...")
        result = await client.call_tool(
            "match_jobs_from_prompt",
            {"skills": ["Python", "PyTorch"], "preferences": None, "limit": 5},
        )

        for block in result.content:
            if hasattr(block, "text"):
                print(json.dumps(json.loads(block.text), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
