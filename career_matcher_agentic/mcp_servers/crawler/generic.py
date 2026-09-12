from typing import Any

from career_matcher_agentic.mcp_servers.crawler.base import BaseCrawler
from career_matcher_agentic.mcp_servers.crawler.firecrawl_client import get_firecrawl_client
from career_matcher_agentic.mcp_servers.crawler.schemas import JobPosting


def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


class GenericFirecrawlCrawler(BaseCrawler):
    """Default crawler for any job board without a dedicated implementation."""

    def discover_job_links(self, listing_url: str, job_category: str) -> list[str]:
        firecrawl = get_firecrawl_client()
        result = firecrawl.map(listing_url, search=job_category)
        links = _get(result, "links") or []
        return [url for link in links if (url := _get(link, "url"))]

    def extract_job(self, job_url: str, job_category: str) -> JobPosting | None:
        firecrawl = get_firecrawl_client()
        result = firecrawl.scrape(
            job_url,
            formats=[
                {
                    "type": "json",
                    "schema": JobPosting.model_json_schema(),
                    "prompt": (
                        "Extract this job posting's title, company, location, remote "
                        "status, requirements, and tech stack. Return nothing if this "
                        f"page is not a job posting relevant to '{job_category}'."
                    ),
                }
            ],
        )
        data = _get(result, "json")
        if not data:
            return None

        try:
            return JobPosting.model_validate({**data, "url": data.get("url") or job_url})
        except Exception:
            return None
