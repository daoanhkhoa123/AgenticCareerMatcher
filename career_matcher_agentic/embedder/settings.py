from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent / ".env"
_ENV_FILE_ENCODING = "utf-8"


class _EmbedderSettings(BaseSettings):
    jina_url: str = "https://api.jina.ai/v1/embeddings"
    jina_timeout_seconds: int = 30
    embedding_dimensions: int = 1024

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding=_ENV_FILE_ENCODING,
        extra="ignore",
    )


EmbedderSettings = _EmbedderSettings()  # type: ignore
