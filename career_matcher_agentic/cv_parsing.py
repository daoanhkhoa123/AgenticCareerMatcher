import json
from pathlib import Path

from pydantic import BaseModel
from pypdf import PdfReader

from career_matcher_agentic.llm.groq_client import get_groq_client

_MODEL = "openai/gpt-oss-120b"

_EXTRACTION_PROMPT = (
    "Extract the following from this CV/resume and respond with ONLY a JSON object matching this "
    'exact shape: {"skills": [str, ...], "projects": [str, ...], "certifications": [str, ...], '
    '"preferences": str | null, "experience": str | null, "education": str | null}\n\n'
    "- skills: every distinct technical skill, programming language, framework, and tool mentioned, "
    "as a flat list of short strings.\n"
    "- projects: notable projects the candidate worked on, as a flat list of short one-line descriptions.\n"
    "- certifications: certification names, as a flat list of short strings.\n"
    "- preferences: any stated role, location, or work-mode (e.g. remote/hybrid) preferences, as a short "
    "string, or null if none are stated.\n"
    "- experience: a brief 2-4 sentence summary of the candidate's work experience, or null if none is present.\n"
    "- education: a brief summary of the candidate's educational background, or null if none is present.\n\n"
    "CV/resume:\n"
)


class CVProfile(BaseModel):
    skills: list[str]
    projects: list[str] = []
    certifications: list[str] = []
    preferences: str | None = None
    experience: str | None = None
    education: str | None = None


def _extract_text(file_path: str) -> str:
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_bytes().decode("utf-8", errors="ignore")


def parse_cv(file_path: str) -> CVProfile:
    text = _extract_text(file_path)

    client = get_groq_client()
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": _EXTRACTION_PROMPT + text}],
        response_format={"type": "json_object"},
    )

    return CVProfile.model_validate(json.loads(response.choices[0].message.content))
