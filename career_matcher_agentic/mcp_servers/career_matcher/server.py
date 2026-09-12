from mcp.server import MCPServer

from career_matcher_agentic.cv_parsing import parse_cv
from career_matcher_agentic.logging.pydantic_logger import setup_logging
from career_matcher_agentic.mcp_servers.career_matcher.matching import match_jobs

mcp = MCPServer("career-matcher")


@mcp.tool()
def match_jobs_from_prompt(
    skills: list[str],
    preferences: str | None = None,
    limit: int = 5,
) -> dict:
    """Search the job database for positions that match a list of skills and preferences provided manually by the user in the chat.

    Returns {"matches": [...], "total_jobs_in_db": int, "last_crawled_at": str | None, "note": str | None}.
    total_jobs_in_db/last_crawled_at describe how much data backs this result, and note (when present)
    is a caveat about match count/data staleness that should be relayed to the user, along with an offer
    to trigger a crawl for fresher/more data.
    """
    return match_jobs(skills=skills, preferences=preferences, limit=limit)


@mcp.tool()
def match_jobs_from_cv(
    file_path: str,
    preferences: str | None = None,
    limit: int = 5,
) -> dict:
    """Parses a candidate's CV file to extract their technical profile, then searches the job database for the best matches.

    Returns {"matches": [...], "total_jobs_in_db": int, "last_crawled_at": str | None, "note": str | None}.
    total_jobs_in_db/last_crawled_at describe how much data backs this result, and note (when present)
    is a caveat about match count/data staleness that should be relayed to the user, along with an offer
    to trigger a crawl for fresher/more data.
    """
    profile = parse_cv(file_path)
    return match_jobs(skills=profile.skills, preferences=preferences, limit=limit)


def main() -> None:
    setup_logging()
    mcp.run()


if __name__ == "__main__":
    main()
