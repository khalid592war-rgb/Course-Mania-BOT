from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    token_encryption_key: str
    session_secret: str
    public_base_url: str = "http://localhost:8000"
    app_env: str = "development"


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
