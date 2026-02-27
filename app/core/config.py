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

    # Turso / libSQL database (optional)
    turso_enabled: bool = False
    turso_db_path: str = ":memory:"
    turso_remote_url: str | None = None  # When set, used as remote_url for embedded replica sync
    turso_auth_token: str | None = None  # Optional auth token for remote Turso database

    # JWT authentication (optional)
    auth_enabled: bool = False
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    auth_username: str | None = "admin"
    auth_password: str | None = "change-me"


settings = Settings()
