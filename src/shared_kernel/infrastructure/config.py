"""Application settings loaded from environment variables."""

import typing

import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str
    database_url_test: str = ""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 24
    jwt_refresh_token_expire_days: int = 7

    resend_api_key: str = ""
    sender_email: str = "noreply@agroconecta.co"

    environment: typing.Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
