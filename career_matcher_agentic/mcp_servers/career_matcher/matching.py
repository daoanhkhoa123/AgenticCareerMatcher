import logging

from career_matcher_agentic.db.models import Job
from career_matcher_agentic.db.session import get_session
from career_matcher_agentic.db.stats import build_staleness_note, get_dataset_stats

logger = logging.getLogger(__name__)


def match_jobs(skills: list[str], preferences: str | None, limit: int) -> dict:
    logger.info("Matching %d skill(s) against jobs (preferences=%r, limit=%d)", len(skills), preferences, limit)

    wanted_skills = {skill.lower() for skill in skills}
    wants_remote = bool(preferences) and "remote" in preferences.lower()

    with get_session() as session:
        total_jobs_in_db, last_crawled_at = get_dataset_stats(session)

        jobs = session.query(Job).all()

        scored: list[tuple[int, Job]] = []
        for job in jobs:
            if wants_remote and not job.remote:
                continue
            overlap = len(wanted_skills & {tech.lower() for tech in job.tech_stack})
            if overlap == 0:
                continue
            scored.append((overlap, job))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        matches = [job.to_dict() for _, job in scored[:limit]]

        note = build_staleness_note(len(matches), total_jobs_in_db, last_crawled_at)
        logger.info("Found %d match(es) out of %d job(s) in database", len(matches), total_jobs_in_db)

        return {
            "matches": matches,
            "total_jobs_in_db": total_jobs_in_db,
            "last_crawled_at": last_crawled_at,
            "note": note,
        }
