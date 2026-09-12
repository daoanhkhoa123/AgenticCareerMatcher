from sqlalchemy import func
from sqlalchemy.orm import Session

from career_matcher_agentic.db.models import Job


def get_dataset_stats(session: Session) -> tuple[int, str | None]:
    total_jobs_in_db = session.query(func.count(Job.id)).scalar()
    last_crawled = session.query(func.max(Job.updated_at)).scalar()
    last_crawled_at = last_crawled.isoformat() if last_crawled is not None else None
    return total_jobs_in_db, last_crawled_at


def build_staleness_note(match_count: int, total_jobs_in_db: int, last_crawled_at: str | None) -> str | None:
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
