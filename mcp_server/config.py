from pydantic_settings import BaseSettings, SettingsConfigDict


class McpSettings(BaseSettings):
    """Local-only settings for the MCP wrapper - never read by the deployed app."""

    model_config = SettingsConfigDict(env_prefix="MCP_", env_file=".env.mcp", extra="ignore")

    # Defaults to the live deployment, since an MCP client (e.g. Claude Desktop)
    # connecting to this server has no separate local API instance to reach -
    # override with MCP_API_BASE_URL to point at a local dev server instead.
    api_base_url: str = "https://nanda-municipal-laws.vercel.app"
    request_timeout_seconds: float = 15.0


settings = McpSettings()
