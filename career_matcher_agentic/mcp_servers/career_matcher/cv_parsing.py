from pathlib import Path

from google.genai import types
from pydantic import BaseModel

from career_matcher_agentic.llm.gemini_client import get_gemini_client

_MODEL = "gemini-3.6-flash"

_EXTRACTION_PROMPT = (
    "Extract every distinct technical skill, programming language, framework, "
    "and tool mentioned in this CV/resume as a flat list of short strings."
)


class CVProfile(BaseModel):
    skills: list[str]


def parse_cv(file_path: str) -> CVProfile:
    path = Path(file_path)
    data = path.read_bytes()

    if path.suffix.lower() == ".pdf":
        contents = [_EXTRACTION_PROMPT, types.Part.from_bytes(data=data, mime_type="application/pdf")]
    else:
        contents = [_EXTRACTION_PROMPT, data.decode("utf-8", errors="ignore")]

    client = get_gemini_client()
    response = client.models.generate_content(
        model=_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CVProfile,
        ),
    )

    if response.parsed is not None:
        return response.parsed
    return CVProfile.model_validate_json(response.text)
