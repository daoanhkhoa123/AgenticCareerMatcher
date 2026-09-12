# `career_matcher_agentic/embedder`

Turns text into vectors via the Jina Embeddings API. Feeds the
`jobs.embedding` column and embeds CV queries for semantic matching.

## Files

- `key_config.py` — reads `JINA_API_KEY` from `embedder/.key`.
- `settings.py` — `EmbedderSettings`: `jina_url`, `jina_timeout_seconds`,
  `embedding_dimensions` (default 1024, also sizes the pgvector column).
- `jina_embedder.py` — `JinaEmbedder`: `embed(texts, task=...)` for
  batches, `__call__(text)` for one string.

## Usage

```python
from career_matcher_agentic.embedder.jina_embedder import JinaEmbedder

embedder = JinaEmbedder()
vectors = embedder.embed(["Python, PyTorch, Docker"], task="retrieval.passage")
```

## Notes

- Use `task="retrieval.passage"` for job postings, `task="retrieval.query"`
  for CV queries — Jina v3 tunes these differently.
- `embedding_dimensions` is the single source of truth for both the API
  request and the DB column width.
