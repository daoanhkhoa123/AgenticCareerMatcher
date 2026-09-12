# `career_matcher_agentic/llm`

Shared Groq client, used by anything in the project that calls an LLM
directly.

## Files

- `key_config.py` — reads `GROQ_API_KEY` from `llm/.key`.
- `groq_client.py` — `get_groq_client()`, a lazy `Groq` client singleton.

## Usage

```python
from career_matcher_agentic.llm.groq_client import get_groq_client

client = get_groq_client()
response = client.chat.completions.create(model="openai/gpt-oss-120b", messages=[...])
```

## Who uses this

- `cv_parsing.py` — extracts CV text, then asks the model for structured
  JSON (skills, projects, certifications, preferences, experience,
  education).
- `mcp_host/llm.py` — the host's tool-calling loop.

Note: the model name (`openai/gpt-oss-120b`) is defined separately in each
consumer, not centralized here.
