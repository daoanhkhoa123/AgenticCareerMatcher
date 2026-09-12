from firecrawl import Firecrawl

from career_matcher_agentic.mcp_servers.crawler.key_config import KeyConfig

_client: Firecrawl | None = None


def get_firecrawl_client() -> Firecrawl:
    global _client
    if _client is None:
        _client = Firecrawl(api_key=KeyConfig.firecrawl_api_key)
    return _client
