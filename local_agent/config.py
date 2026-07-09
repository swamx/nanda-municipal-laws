from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Local-only settings for the agent simulator - never read by the deployed app."""

    model_config = SettingsConfigDict(env_prefix="AGENT_", env_file=".env.agent", extra="ignore")

    # Defaults to the local dev server, not the live Vercel deployment, since
    # this tool exists to "simulate things locally" - override with
    # AGENT_API_BASE_URL (or --api-base-url) to point at a deployed instance.
    api_base_url: str = "http://localhost:8000"

    # None means "whatever your Claude Code session's current default model is".
    claude_model: str | None = None
    claude_timeout_seconds: float = 90.0


settings = AgentSettings()
