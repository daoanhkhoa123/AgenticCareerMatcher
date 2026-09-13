from typing import Literal

import requests

from career_matcher_agentic.embedder.key_config import KeyConfig
from career_matcher_agentic.embedder.settings import EmbedderSettings

JinaModel = Literal["jina-embeddings-v5-omni-small"]


class JinaEmbedder:
    def __init__(
        self, model: JinaModel = "jina-embeddings-v5-omni-small", dimensions: int = EmbedderSettings.embedding_dimensions
    ) -> None:
        self._model = model
        self._dimensions = dimensions
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KeyConfig.jina_key}",
        }

    @property
    def model(self) -> str:
        return self._model

    def embed(self, texts: list[str], task: Literal["text-matching", "retrieval.query", "retrieval.passage"] = "text-matching") -> list[list[float]]:
        payload = {
            "model": self._model,
            "task": task,
            "dimensions": self._dimensions,
            "input": texts,
        }

        response = requests.post(
            EmbedderSettings.jina_url,
            headers=self._headers,
            json=payload,
            timeout=EmbedderSettings.jina_timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()["data"]
        return [item["embedding"] for item in data]

    def __call__(self, text: str) -> list[float]:
        return self.embed([text])[0]
