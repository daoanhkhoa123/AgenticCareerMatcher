from mcp.server import MCPServer

from career_matcher_agentic.logging.pydantic_logger import setup_logging
from career_matcher_agentic.mcp_servers.crawler.crawling import run_crawler

mcp = MCPServer("job-crawler")


@mcp.tool()
def trigger_crawler(target_url: str, job_category: str) -> dict:
    """Scrapes a given job board URL for a specific job category and saves the postings to the database."""
    return run_crawler(target_url, job_category)


def main() -> None:
    setup_logging()
    mcp.run()


if __name__ == "__main__":
    main()
