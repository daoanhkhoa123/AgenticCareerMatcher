from groq import Groq

from career_matcher_agentic.llm.key_config import KeyConfig

_client: Groq | None = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=KeyConfig.groq_api_key)
    return _client
