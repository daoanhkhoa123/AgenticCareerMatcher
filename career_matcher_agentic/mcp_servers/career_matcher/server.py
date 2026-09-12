from mcp.server import MCPServer

from career_matcher_agentic.mcp_servers.career_matcher.cv_parsing import parse_cv
from career_matcher_agentic.mcp_servers.career_matcher.matching import match_jobs

mcp = MCPServer("career-matcher")


@mcp.tool()
def match_jobs_from_prompt(
    skills: list[str],
    preferences: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Search the job database for positions that match a list of skills and preferences provided manually by the user in the chat."""
    return match_jobs(skills=skills, preferences=preferences, limit=limit)


@mcp.tool()
def match_jobs_from_cv(
    file_path: str,
    preferences: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Parses a candidate's CV file to extract their technical profile, then searches the job database for the best matches."""
    profile = parse_cv(file_path)
    return match_jobs(skills=profile.skills, preferences=preferences, limit=limit)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
