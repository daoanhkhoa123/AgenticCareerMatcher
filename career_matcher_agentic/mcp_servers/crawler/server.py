from mcp.server import MCPServer

from career_matcher_agentic.logging.pydantic_logger import setup_logging
from career_matcher_agentic.mcp_servers.crawler.crawling import run_crawler
from career_matcher_agentic.mcp_servers.crawler.registry import list_supported_sites as _list_supported_sites

mcp = MCPServer("job-crawler")


@mcp.tool()
def list_supported_sites() -> list[dict]:
    """Lists job boards with dedicated, higher-quality crawler support (domain + description).

    Check this before asking the user for an arbitrary URL - a site on this list will give
    better results than an unlisted one, which falls back to slower/costlier generic extraction.
    """
    return _list_supported_sites()


@mcp.tool()
def trigger_crawler(target_url: str, job_category: str) -> dict:
    """Scrapes a given job board URL for a specific job category and saves the postings to the database.

    Sites returned by list_supported_sites have dedicated support and give better results;
    any other URL falls back to slower/costlier generic LLM-based extraction.
    """
    return run_crawler(target_url, job_category)


def main() -> None:
    setup_logging()
    mcp.run()


if __name__ == "__main__":
    main()
