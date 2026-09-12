from sqlalchemy import func

from career_matcher_agentic.db.models import Job
from career_matcher_agentic.db.session import get_session


def match_jobs(skills: list[str], preferences: str | None, limit: int) -> dict:
    wanted_skills = {skill.lower() for skill in skills}
    wants_remote = bool(preferences) and "remote" in preferences.lower()

    with get_session() as session:
        total_jobs_in_db = session.query(func.count(Job.id)).scalar()
        last_crawled = session.query(func.max(Job.updated_at)).scalar()
        last_crawled_at = last_crawled.isoformat() if last_crawled is not None else None

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

        note = _build_note(len(matches), total_jobs_in_db, last_crawled_at)

        return {
            "matches": matches,
            "total_jobs_in_db": total_jobs_in_db,
            "last_crawled_at": last_crawled_at,
            "note": note,
        }


def _build_note(match_count: int, total_jobs_in_db: int, last_crawled_at: str | None) -> str | None:
    crawled_phrase = f"since {last_crawled_at}" if last_crawled_at else "at all"

    if match_count == 0:
        return (
            f"No matches found. The database only has {total_jobs_in_db} job(s) and hasn't "
            f"been crawled {crawled_phrase}. Consider crawling more listings before trusting this result."
        )
    if match_count <= 2:
        return (
            f"Only {match_count} match(es) found out of {total_jobs_in_db} job(s) in the database "
            f"(last crawled {crawled_phrase}) - this is a small sample and may not reflect the best options."
        )
    return None
