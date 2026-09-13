import logging

from career_matcher_agentic.db.models import Job
from career_matcher_agentic.db.session import get_session
from career_matcher_agentic.embedder.jina_embedder import JinaEmbedder
from career_matcher_agentic.mcp_servers.crawler.registry import get_crawler
from career_matcher_agentic.mcp_servers.crawler.schemas import JobPosting

logger = logging.getLogger(__name__)

_embedder = JinaEmbedder()


def run_crawler(target_url: str, job_category: str) -> dict:
    crawler = get_crawler(target_url)
    logger.info("Crawling %s for category '%s' using %s", target_url, job_category, type(crawler).__name__)

    try:
        postings = crawler.crawl(target_url, job_category)
    except Exception as exc:
        logger.exception("Crawl failed for %s", target_url)
        return {
            "target_url": target_url,
            "job_category": job_category,
            "error": f"{type(exc).__name__}: {exc}",
        }
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


def _build_embedding_text(posting: JobPosting) -> str:
    return f"{posting.title}\n{posting.company}\n{posting.requirements}\n{', '.join(posting.tech_stack)}"


def _persist(postings: list[JobPosting], job_category: str) -> tuple[int, int]:
    saved = 0
    updated = 0

    embeddings: list[list[float]] = []
    if postings:
        texts = [_build_embedding_text(posting) for posting in postings]
        embeddings = _embedder.embed(texts, task="retrieval.passage")

    with get_session() as session:
        for posting, embedding in zip(postings, embeddings):
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
            job.embedding = embedding
            job.embedding_model = _embedder.model

    return saved, updated
