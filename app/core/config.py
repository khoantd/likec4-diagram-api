"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings loaded from environment."""

    model_config = SettingsConfigDict(env_prefix="LIKEC4_API_", env_file=".env")

    app_name: str = "LikeC4 Diagram API"
    debug: bool = False

    # AI generation (optional): OpenAI-compatible API (OpenAI, LiteLLM proxy, Azure, etc.)
    ai_enabled: bool = False
    openai_api_key: str = ""  # Use placeholder e.g. sk-1234 if LiteLLM does not validate
    openai_base_url: str | None = None  # e.g. https://api.openai.com/v1
    litellm_base_url: str | None = None  # LiteLLM proxy base URL (e.g. https://litellm.example.com/v1); overrides openai_base_url when set
    ai_model: str = "gpt-4o-mini"  # For LiteLLM use model name like openai/gpt-4o or anthropic/claude-3-5-sonnet


settings = Settings()
