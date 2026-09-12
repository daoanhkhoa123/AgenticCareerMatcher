from dataclasses import dataclass
from urllib.parse import urlparse

from career_matcher_agentic.mcp_servers.crawler.base import BaseCrawler
from career_matcher_agentic.mcp_servers.crawler.generic import GenericFirecrawlCrawler


@dataclass
class RegisteredSite:
    crawler_cls: type[BaseCrawler]
    description: str


_REGISTRY: dict[str, RegisteredSite] = {}


def register(domain: str, description: str):
    def decorator(cls: type[BaseCrawler]) -> type[BaseCrawler]:
        _REGISTRY[domain] = RegisteredSite(crawler_cls=cls, description=description)
        return cls

    return decorator


def get_crawler(url: str) -> BaseCrawler:
    domain = urlparse(url).netloc.lower()
    site = _REGISTRY.get(domain)
    crawler_cls = site.crawler_cls if site else GenericFirecrawlCrawler
    return crawler_cls()


def list_supported_sites() -> list[dict]:
    return [{"domain": domain, "description": site.description} for domain, site in _REGISTRY.items()]


# Imported last so each site module's @register(...) runs against the names
# defined above. Site modules import `register` back from this module, which
# is safe here because they're only reached once this module is fully loaded.
from career_matcher_agentic.mcp_servers.crawler import sites  # noqa: E402,F401
