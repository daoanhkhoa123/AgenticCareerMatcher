from career_matcher_agentic.cv_parsing import CVProfile
from career_matcher_agentic.db.models import Job
from career_matcher_agentic.db.session import get_session
from career_matcher_agentic.db.stats import build_staleness_note, get_dataset_stats
from career_matcher_agentic.embedder.jina_embedder import JinaEmbedder

_embedder = JinaEmbedder()


def _build_query_text(profile: CVProfile, preferences: str | None) -> str:
    parts = [
        ", ".join(profile.skills),
        ", ".join(profile.projects),
        ", ".join(profile.certifications),
        profile.experience,
        profile.education,
        profile.preferences,
        preferences,
    ]
    return "\n".join(part for part in parts if part)


def match_jobs_by_embedding(profile: CVProfile, preferences: str | None, limit: int) -> dict:
    query_vector = _embedder.embed([_build_query_text(profile, preferences)], task="retrieval.query")[0]

    with get_session() as session:
        total_jobs_in_db, last_crawled_at = get_dataset_stats(session)

        jobs = (
            session.query(Job)
            .filter(Job.embedding.is_not(None))
            .order_by(Job.embedding.cosine_distance(query_vector))
            .limit(limit)
            .all()
        )
        matches = [job.to_dict() for job in jobs]
        note = build_staleness_note(len(matches), total_jobs_in_db, last_crawled_at)

        return {
            "matches": matches,
            "total_jobs_in_db": total_jobs_in_db,
            "last_crawled_at": last_crawled_at,
            "note": note,
        }
