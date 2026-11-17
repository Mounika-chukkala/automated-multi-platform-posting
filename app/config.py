
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bluesky_handle: str | None = None
    bluesky_app_password: str | None = None
    mastodon_instance_url: str | None = None
    mastodon_access_token: str | None = None

    wordpress_client_id: str | None = None
    wordpress_client_secret: str | None = None
    wordpress_access_token: str | None = None
    wordpress_site_url: str | None = None

    tumblr_client_id: str | None = None
    tumblr_client_secret: str | None = None
    tumblr_access_token: str | None = None
    tumblr_refresh_token: str | None = None
    tumblr_blog_identifier: str | None = None

    devto_api_key: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
