import logging

from career_matcher_agentic.db.models import Job
from career_matcher_agentic.db.session import get_session
from career_matcher_agentic.mcp_servers.crawler.registry import get_crawler
from career_matcher_agentic.mcp_servers.crawler.schemas import JobPosting

logger = logging.getLogger(__name__)


def run_crawler(target_url: str, job_category: str) -> dict:
    crawler = get_crawler(target_url)
    logger.info("Crawling %s for category '%s' using %s", target_url, job_category, type(crawler).__name__)

    postings = crawler.crawl(target_url, job_category)
    logger.info("Extracted %d job posting(s) from %s", len(postings), target_url)

    saved, updated = _persist(postings, job_category)
    logger.info("Persisted results: %d saved, %d updated", saved, updated)

    return {
        "target_url": target_url,
        "job_category": job_category,
        "jobs_found": len(postings),
        "jobs_saved": saved,
        "jobs_updated": updated,
    }


def _persist(postings: list[JobPosting], job_category: str) -> tuple[int, int]:
    saved = 0
    updated = 0
    with get_session() as session:
        for posting in postings:
            job = session.query(Job).filter_by(url=posting.url).first()
            if job is None:
                job = Job(url=posting.url)
                session.add(job)
                saved += 1
            else:
                updated += 1

            job.title = posting.title
            job.company = posting.company
            job.category = job_category
            job.location = posting.location
            job.remote = posting.remote
            job.requirements = posting.requirements
            job.tech_stack = posting.tech_stack

    return saved, updated
