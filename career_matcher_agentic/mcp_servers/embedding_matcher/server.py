from mcp.server import MCPServer

from career_matcher_agentic.cv_parsing import parse_cv
from career_matcher_agentic.logging.pydantic_logger import setup_logging
from career_matcher_agentic.mcp_servers.embedding_matcher.matching import match_jobs_by_embedding

mcp = MCPServer("embedding-matcher")


@mcp.tool()
def match_jobs_from_cv_embedding(
    file_path: str,
    preferences: str | None = None,
    limit: int = 5,
) -> dict:
    """Parses a candidate's CV file and ranks job postings by semantic similarity (embeddings),
    not exact skill-keyword overlap - use this to surface conceptually related roles a keyword
    search would miss (e.g. different tech naming, adjacent skillsets).

    Returns {"matches": [...], "total_jobs_in_db": int, "last_crawled_at": str | None, "note": str | None}.
    total_jobs_in_db/last_crawled_at describe how much data backs this result, and note (when present)
    is a caveat about match count/data staleness that should be relayed to the user, along with an offer
    to trigger a crawl for fresher/more data.
    """
    profile = parse_cv(file_path)
    return match_jobs_by_embedding(profile, preferences=preferences, limit=limit)


def main() -> None:
    setup_logging()
    mcp.run()


if __name__ == "__main__":
    main()
