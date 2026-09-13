import logging
from abc import ABC, abstractmethod

from career_matcher_agentic.mcp_servers.crawler.schemas import JobPosting
from career_matcher_agentic.mcp_servers.crawler.settings import CrawlerSettings

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    def __init__(self) -> None:
        self.logger = logger.getChild(self.__class__.__name__)

    @abstractmethod
    def discover_job_links(self, listing_url: str, job_category: str) -> list[str]: ...

    @abstractmethod
    def extract_job(self, job_url: str, job_category: str) -> JobPosting | None: ...

    def crawl(self, listing_url: str, job_category: str) -> list[JobPosting]:
        links = self.discover_job_links(listing_url, job_category)
        self.logger.info("Discovered %d job link(s) on %s", len(links), listing_url)

        limit = CrawlerSettings.max_jobs_per_crawl
        if len(links) > limit:
            self.logger.info("Capping crawl at %d of %d discovered link(s)", limit, len(links))
            links = links[:limit]

        postings = [p for link in links if (p := self.extract_job(link, job_category)) is not None]
        failed = len(links) - len(postings)
        if failed:
            self.logger.warning("%d of %d link(s) failed to extract on %s", failed, len(links), listing_url)

        return postings
