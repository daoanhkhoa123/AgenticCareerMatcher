from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

from career_matcher_agentic.mcp_servers.crawler.base import BaseCrawler
from career_matcher_agentic.mcp_servers.crawler.firecrawl_client import get_firecrawl_client
from career_matcher_agentic.mcp_servers.crawler.registry import register
from career_matcher_agentic.mcp_servers.crawler.schemas import JobPosting
from career_matcher_agentic.mcp_servers.crawler.settings import CrawlerSettings


@register("itviec.com")
class ItViecCrawler(BaseCrawler):
    """CSS-selector-based crawler for itviec.com (https://itviec.com/it-jobs/<tag>),
    whose listing/detail pages have a stable, known structure that doesn't need
    LLM-driven extraction."""

    def discover_job_links(self, listing_url: str, job_category: str) -> list[str]:
        links: list[str] = []
        url: str | None = listing_url

        for _ in range(CrawlerSettings.max_listing_pages):
            if not url:
                break
            soup = BeautifulSoup(self._fetch_html(url), "html.parser")

            for heading in soup.select("h3[data-search--job-selection-target='jobTitle']"):
                anchor = heading.find("a", href=True)
                if anchor:
                    links.append(_clean_url(anchor["href"]))

            next_link = soup.select_one("a[rel='next']")
            url = _absolute_url(next_link["href"]) if next_link and next_link.get("href") else None

        return links

    def extract_job(self, job_url: str, job_category: str) -> JobPosting | None:
        soup = BeautifulSoup(self._fetch_html(job_url), "html.parser")

        title_el = soup.select_one("h1")
        company_el = soup.select_one(".employer-name")
        if not title_el or not company_el:
            return None

        tech_stack: list[str] = []
        skills_label = soup.find("div", string=lambda s: bool(s) and s.strip() == "Skills:")
        if skills_label:
            tags_container = skills_label.find_next_sibling("div")
            if tags_container:
                tech_stack = [a.get_text(strip=True) for a in tags_container.select("a")]

        location_el = soup.select_one(".job-show-info .normal-text.text-rich-grey")
        location = location_el.get_text(strip=True) if location_el else None

        work_type_el = soup.select_one(".job-show-info .preview-header-item .ms-1")
        work_type = work_type_el.get_text(strip=True).lower() if work_type_el else ""
        remote = "remote" in work_type

        requirements = ""
        requirements_heading = soup.find("h2", string=lambda s: bool(s) and "skills and experience" in s.lower())
        if requirements_heading:
            section = requirements_heading.find_parent("div", class_="paragraph")
            if section:
                requirements = section.get_text(" ", strip=True)

        return JobPosting(
            title=title_el.get_text(strip=True),
            company=company_el.get_text(strip=True),
            url=job_url,
            location=location,
            remote=remote,
            requirements=requirements,
            tech_stack=tech_stack,
        )

    @staticmethod
    def _fetch_html(url: str) -> str:
        firecrawl = get_firecrawl_client()
        result = firecrawl.scrape(url, formats=["html"])
        if isinstance(result, dict):
            return result.get("html") or ""
        return getattr(result, "html", None) or ""


def _absolute_url(href: str) -> str:
    if href.startswith("http"):
        return href
    return f"https://itviec.com{href}"


def _clean_url(href: str) -> str:
    url = _absolute_url(href)
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
