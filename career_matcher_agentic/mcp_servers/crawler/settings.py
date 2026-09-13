from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent / ".env"
_ENV_FILE_ENCODING = "utf-8"


class _CrawlerSettings(BaseSettings):
    max_listing_pages: int = 3
    max_jobs_per_crawl: int = 10
    max_retries: int = 3
    retry_base_delay_seconds: float = 2.0

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding=_ENV_FILE_ENCODING,
        extra="ignore",
    )


CrawlerSettings = _CrawlerSettings()  # type: ignore
