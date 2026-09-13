import logging
import re
import time
from typing import Any, Callable, TypeVar

from firecrawl import Firecrawl
from firecrawl.v2.utils.error_handler import RateLimitError

from career_matcher_agentic.mcp_servers.crawler.key_config import KeyConfig
from career_matcher_agentic.mcp_servers.crawler.settings import CrawlerSettings

logger = logging.getLogger(__name__)

_client: Firecrawl | None = None
_RETRY_AFTER_RE = re.compile(r"retry after (\d+)s")

_T = TypeVar("_T")


def get_firecrawl_client() -> Firecrawl:
    global _client
    if _client is None:
        _client = Firecrawl(api_key=KeyConfig.firecrawl_api_key)
    return _client


def _rate_limit_delay(exc: RateLimitError, attempt: int) -> float:
    """Prefer the server's own reset window over guessing."""
    header = getattr(exc.response, "headers", {}).get("Retry-After") if exc.response is not None else None
    if header:
        try:
            return float(header)
        except ValueError:
            pass

    match = _RETRY_AFTER_RE.search(str(exc))
    if match:
        return float(match.group(1))

    return CrawlerSettings.retry_base_delay_seconds * (2**attempt)


def call_with_retry(fn: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
    """Calls a Firecrawl SDK method, retrying on rate limit (429) instead of
    letting one throttled request fail the whole crawl."""
    for attempt in range(CrawlerSettings.max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except RateLimitError as exc:
            if attempt == CrawlerSettings.max_retries:
                raise
            delay = _rate_limit_delay(exc, attempt)
            logger.warning(
                "Firecrawl rate limit hit (attempt %d/%d), retrying in %.1fs",
                attempt + 1,
                CrawlerSettings.max_retries,
                delay,
            )
            time.sleep(delay)

    raise AssertionError("unreachable")
