from abc import ABC, abstractmethod

from career_matcher_agentic.mcp_servers.crawler.schemas import JobPosting


class BaseCrawler(ABC):
    @abstractmethod
    def discover_job_links(self, listing_url: str, job_category: str) -> list[str]: ...

    @abstractmethod
    def extract_job(self, job_url: str, job_category: str) -> JobPosting | None: ...

    def crawl(self, listing_url: str, job_category: str) -> list[JobPosting]:
        links = self.discover_job_links(listing_url, job_category)
        return [p for link in links if (p := self.extract_job(link, job_category)) is not None]
