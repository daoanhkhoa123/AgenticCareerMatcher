from google import genai

from career_matcher_agentic.llm.key_config import KeyConfig

_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=KeyConfig.gemini_api_key)
    return _client
