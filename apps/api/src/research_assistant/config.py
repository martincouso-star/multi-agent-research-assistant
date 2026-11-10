from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parents[3]
_ENV_FILES = tuple(
    str(path)
    for path in (_REPO_ROOT / ".env", Path.cwd() / ".env")
    if path.is_file()
)


class Settings(BaseSettings):
    """Runtime configuration. Defaults run fully offline."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"

    search_provider: str = "mock"
    tavily_api_key: str = ""
    search_results_per_query: int = Field(default=3, ge=1, le=8)

    max_revisions: int = Field(default=1, ge=0, le=3)
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
