# `career_matcher_agentic/mcp_servers/crawler`

MCP server (`job-crawler-mcp`) that scrapes job board listings into the
shared `jobs` table. Kept separate from the matching servers since scraping
is a much less predictable operation.

## Files

- `base.py` — `BaseCrawler`: `discover_job_links`, `extract_job`, and
  `crawl()` chaining the two.
- `schemas.py` — `JobPosting`, the shape every crawler produces.
- `registry.py` — maps a domain to a crawler implementation; `get_crawler(url)`
  falls back to `GenericFirecrawlCrawler`.
- `generic.py` — `GenericFirecrawlCrawler`: Firecrawl-based LLM extraction
  for any unregistered site.
- `sites/itviec.py` — `ItViecCrawler`: CSS-selector-based crawler for
  itviec.com, with pagination.
- `firecrawl_client.py` — lazy Firecrawl client from `FIRECRAWL_API_KEY`.
- `settings.py` — `CrawlerSettings` (`max_listing_pages`, default 3).
- `crawling.py` — `run_crawler(target_url, job_category)`: runs the right
  crawler, upserts results by `url`, batch-embeds via Jina.
- `server.py` — the `MCPServer("job-crawler")` instance and tools.

## Tools

- `trigger_crawler(target_url, job_category)` — scrape a listing page and
  upsert postings.
- `list_supported_sites()` — sites with a dedicated crawler.

## Running it

```bash
uv run job-crawler-mcp
```

Requires `FIRECRAWL_API_KEY` in `mcp_servers/crawler/.key`.

## Notes

Adding a new site is one new `sites/<name>.py` module subclassing
`BaseCrawler` and registering with `@register(...)` — no existing code to
touch.
