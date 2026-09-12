from pydantic import BaseModel


class JobPosting(BaseModel):
    title: str
    company: str
    url: str
    location: str | None = None
    remote: bool = False
    requirements: str
    tech_stack: list[str]
