from career_matcher_agentic.db.models import Job
from career_matcher_agentic.db.session import get_session


def match_jobs(skills: list[str], preferences: str | None, limit: int) -> list[dict]:
    wanted_skills = {skill.lower() for skill in skills}
    wants_remote = bool(preferences) and "remote" in preferences.lower()

    with get_session() as session:
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

        return [job.to_dict() for _, job in scored[:limit]]
