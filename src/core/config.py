from functools import lru_cache
from pathlib import Path
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


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
    SECRET_KEY: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:pass@localhost:5432/db", env="DATABASE_URL"
    )

    # Neo4j
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")

    # AWS S3
    AWS_ACCESS_KEY_ID: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="ap-south-1", env="AWS_REGION")
    S3_BUCKET_NAME: str = Field(default="", env="S3_BUCKET_NAME")

    # AI Models
    GOOGLE_API_KEY: str = Field(default="", env="GOOGLE_API_KEY")
    GEMINI_EMBEDDING_MODEL: str = Field(
        default="models/embedding-001", env="GEMINI_EMBEDDING_MODEL"
    )
    GEMINI_MODEL_NAME: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL_NAME")

    # Vector Store
    VECTOR_COLLECTION_NAME: str = Field(
        default="knowflow_vector_db", env="VECTOR_COLLECTION_NAME"
    )
    CHUNK_SIZE: int = Field(default=700)
    CHUNK_OVERLAP: int = Field(default=80)
    TOP_K_RESULTS: int = Field(default=8)

    # Graph Store
    GRAPH_BATCH_SIZE: int = Field(default=100)
    GRAPH_MAX_NODES: int = Field(default=1000)
    GRAPH_MAX_RELATIONSHIPS: int = Field(default=5000)

    # Rate Limiting
    RATE_LIMIT_CALLS: int = Field(default=100, env="RATE_LIMIT_CALLS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    RATE_LIMIT_EXCLUDED_PATHS: set[str] = Field(default={"/health", "/health/detailed"})

    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="List of allowed CORS origins. Use ['*'] to allow all origins.",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
