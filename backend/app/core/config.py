# config.py
# Application configuration via environment variables.
# Uses pydantic-settings for validation and .env file support.

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    GWA_API_BASE_URL: str = "https://globalwindatlas.info/api/gwa/custom"

    class Config:
        env_file = ".env"

settings = Settings()