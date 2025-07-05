from functools import lru_cache
from pathlib import Path
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "knowflow"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Environment
    ENV: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = Field(default="logs/knowflow.log", env="LOG_FILE")
    LOG_ROTATION: str = Field(default="midnight", env="LOG_ROTATION")
    LOG_RETENTION: int = Field(default=30, env="LOG_RETENTION")

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=1, env="WORKERS")
    RELOAD: bool = Field(default=False, env="RELOAD")

    # Security
    SECRET_KEY: str = Field(default="your-secret-key", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./knowflow.db", env="DATABASE_URL")

    # Rate Limiting
    RATE_LIMIT_CALLS: int = Field(default=100, env="RATE_LIMIT_CALLS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    RATE_LIMIT_EXCLUDED_PATHS: set[str] = Field(
        default={"/health", "/health/detailed"}, env="RATE_LIMIT_EXCLUDED_PATHS"
    )

    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="List of allowed CORS origins. Use ['*'] to allow all origins.",
    )

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent.parent

    @property
    def log_file_path(self) -> Path:
        return self.base_dir / self.LOG_FILE


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
