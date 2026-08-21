from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = Field(default="dev", alias="ENV")
    database_url: str = Field(alias="DATABASE_URL")
    session_secret: str = Field(alias="SESSION_SECRET")
    session_max_age_seconds: int = Field(default=60 * 60 * 24 * 7, alias="SESSION_MAX_AGE_SECONDS")

    # Bootstrap admin — only used to seed the single admin user on first startup
    # if the users table is empty. Ignored after that; change the password via
    # the app itself from then on.
    admin_email: str = Field(alias="ADMIN_EMAIL")
    admin_password: str = Field(alias="ADMIN_PASSWORD")

    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # Meta Marketing API — required from Phase 2 onward. Left optional here
    # (not required=True at the Settings level) so the app still boots
    # cleanly before these are configured; meta/client.py fails loudly if a
    # caller actually tries to use it without them.
    meta_app_id: str | None = Field(default=None, alias="META_APP_ID")
    meta_app_secret: str | None = Field(default=None, alias="META_APP_SECRET")
    meta_access_token: str | None = Field(default=None, alias="META_ACCESS_TOKEN")
    meta_default_ad_account_id: str | None = Field(default=None, alias="META_DEFAULT_AD_ACCOUNT_ID")
    meta_api_version: str = Field(default="v26.0", alias="META_API_VERSION")

    # Google Analytics 4 — required from Phase 5 onward. The service account
    # key is stored as raw JSON in one env var (not a file path) — simpler
    # to inject on Coolify than mounting a secret file, and google-auth
    # supports building credentials straight from a parsed dict.
    google_service_account_json: str | None = Field(default=None, alias="GOOGLE_SERVICE_ACCOUNT_JSON")
    google_project_id: str | None = Field(default=None, alias="GOOGLE_PROJECT_ID")
    ga4_property_id: str | None = Field(default=None, alias="GA4_PROPERTY_ID")

    # Command Center — required from Phase 6 onward.
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-5", alias="ANTHROPIC_MODEL")

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
