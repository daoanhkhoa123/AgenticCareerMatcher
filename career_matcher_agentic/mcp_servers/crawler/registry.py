from urllib.parse import urlparse

from career_matcher_agentic.mcp_servers.crawler.base import BaseCrawler
from career_matcher_agentic.mcp_servers.crawler.generic import GenericFirecrawlCrawler

_REGISTRY: dict[str, type[BaseCrawler]] = {}


def register(domain: str):
    def decorator(cls: type[BaseCrawler]) -> type[BaseCrawler]:
        _REGISTRY[domain] = cls
        return cls

    return decorator


def get_crawler(url: str) -> BaseCrawler:
    domain = urlparse(url).netloc.lower()
    crawler_cls = _REGISTRY.get(domain, GenericFirecrawlCrawler)
    return crawler_cls()


# Imported last so each site module's @register(...) runs against the names
# defined above. Site modules import `register` back from this module, which
# is safe here because they're only reached once this module is fully loaded.
from career_matcher_agentic.mcp_servers.crawler import sites  # noqa: E402,F401
