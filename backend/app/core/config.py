# config.py
# Application configuration via environment variables.
# Uses pydantic-settings for validation and .env file support.

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "development"
    GWA_API_BASE_URL: str = "https://globalwindatlas.info/api/gis/country"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()