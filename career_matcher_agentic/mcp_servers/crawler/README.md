# `career_matcher_agentic/mcp_servers/crawler`

A separate MCP server (`job-crawler-mcp`) whose job is to scrape job board
listings into the shared `jobs` table. It's its own server, not a tool
tacked onto `career_matcher`, because scraping arbitrary websites is a
fundamentally less predictable operation (many domains, different HTML,
anti-bot issues) than querying the local database — see `mcp_host/README.md`
for the fuller reasoning.

## Files

- **`base.py`** — `BaseCrawler`, the interface every crawler implementation
  follows: `discover_job_links(listing_url, job_category)` finds individual
  posting links on a listing page, `extract_job(job_url, job_category)`
  turns one posting page into a `JobPosting`, and the concrete `crawl(...)`
  just chains the two (discover, then extract each link, dropping `None`s).
- **`schemas.py`** — `JobPosting`, the Pydantic shape every crawler
  implementation must produce: `title`, `company`, `url`, `location`,
  `remote`, `requirements`, `tech_stack`.
- **`registry.py`** — maps a domain to a `BaseCrawler` implementation.
  `@register(domain, description=...)` self-registers a class (both the
  crawler and a human-facing description, exposed via
  `list_supported_sites()`); `get_crawler(url)` looks up the URL's domain
  and falls back to `GenericFirecrawlCrawler` for anything unregistered.
- **`generic.py`** — `GenericFirecrawlCrawler`, the fallback used for any
  site without a dedicated implementation. `discover_job_links` uses
  Firecrawl's `map(listing_url, search=job_category)` (1 credit/call);
  `extract_job` uses `scrape(job_url, formats=[{"type": "json", "schema":
  JobPosting.model_json_schema(), ...}])` — LLM-driven structured extraction,
  so it needs no per-site selectors but costs more and is less reliable
  than a dedicated crawler.
- **`sites/itviec.py`** — `ItViecCrawler`, a dedicated, CSS-selector-based
  implementation for itviec.com (`@register("itviec.com", description=...)`).
  Fetches raw HTML through Firecrawl (`formats=["html"]`) and parses it with
  BeautifulSoup against itviec's actual markup — cheaper and more reliable
  than LLM extraction since the site's structure is known and stable.
  Handles pagination (`a[rel='next']`, capped at `CrawlerSettings.max_listing_pages`).
  `sites/__init__.py` imports this module so its `@register` runs; see the
  comment in `registry.py` for why that import sits at the *bottom* of the
  file rather than the top (avoiding a circular import between the two).
- **`firecrawl_client.py`** — `get_firecrawl_client()`, a lazy `Firecrawl`
  client singleton built from `FIRECRAWL_API_KEY` (`key_config.py`, reading
  a local `.key` file).
- **`settings.py`** — `CrawlerSettings`, non-secret config from a local
  `.env` file (currently just `max_listing_pages`, default 3).
- **`crawling.py`** — `run_crawler(target_url, job_category)`: resolves the
  right crawler via the registry, runs it, then `_persist`s the results —
  upserting each `JobPosting` into `Job` by `url` (update if a row with that
  URL exists, insert otherwise), batch-embedding all of them in one call via
  `JinaEmbedder` (`task="retrieval.passage"`) and storing the vector in
  `Job.embedding`/`Job.embedding_model` so they're immediately searchable by
  `embedding_matcher`. Logs progress at `INFO` (captured by `setup_logging()`).
- **`server.py`** — the `MCPServer("job-crawler")` instance, its two tools,
  and `main()`.

## Tools

- **`trigger_crawler(target_url, job_category)`** — scrape a listing page
  and upsert the postings.
- **`list_supported_sites()`** — domains with a dedicated crawler
  (currently just itviec.com) and why they're worth preferring over an
  arbitrary URL.

## Running it

```bash
uv run job-crawler-mcp
# or: uv run python -m career_matcher_agentic.mcp_servers.crawler.server
```

Requires `FIRECRAWL_API_KEY` in `mcp_servers/crawler/.key` (see `.key.example`).

## Design notes

- **Two-stage crawling, not one.** Extracting everything from a listing
  page's summary cards is unreliable; visiting each posting's own page
  (`discover_job_links` then `extract_job` per link) gets fuller, more
  accurate data at the cost of more requests.
- **Adding a new site means one new file, not touching existing code.** A
  new `sites/<name>.py` module subclassing `BaseCrawler` (or
  `GenericFirecrawlCrawler`, overriding just `discover_job_links` if only
  link discovery needs site-specific handling) and self-registering with
  `@register(...)` is the entire integration surface.
- **Every upsert re-embeds, even on update.** `_persist` computes a fresh
  embedding for every posting on every crawl run, not just new rows — so a
  posting whose requirements/tech stack changed on a re-crawl gets a
  correspondingly updated vector, never a stale one.
