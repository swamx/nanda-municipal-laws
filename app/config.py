from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_atlas_conn_str: str
    mongodb_db_name: str = "mithackathon"
    cors_origins: str = "*"

    # Fail fast rather than hang until the serverless function's own timeout -
    # a cold Vercel invocation with a bad/unreachable Atlas URI should error
    # in seconds, not eat the whole request budget.
    mongo_connect_timeout_ms: int = 5000
    mongo_server_selection_timeout_ms: int = 5000

    # Shared-secret gate for POST /ingest, since it triggers outbound fetches
    # and Atlas writes - leave unset only for local/demo use. If unset, the
    # endpoint stays open (hackathon-demo default); set it before sharing a
    # public deployment URL.
    ingest_api_key: str | None = None
    ingest_max_urls: int = 10

    rate_limit_per_minute: int = 10
    ingest_rate_limit_per_minute: int = 1

    app_version: str = "0.1.0"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
