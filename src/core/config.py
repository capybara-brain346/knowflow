from functools import lru_cache
from pathlib import Path
from typing import Optional, List
import json
import boto3
from botocore.exceptions import ClientError
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


def get_aws_secret(secret_name: str, region_name: str = "ap-south-1") -> dict:
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response["SecretString"]
        return dict(json.loads(secret))
    except ClientError as e:
        raise e


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
    SECRET_KEY: str = Field(default="")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Database
    DATABASE_URL: str = Field(default="")

    # Neo4j
    NEO4J_URI: str = Field(default="")
    NEO4J_USER: str = Field(default="")
    NEO4J_PASSWORD: str = Field(default="")

    # AWS S3
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_REGION: str = Field(default="ap-south-1")
    S3_BUCKET_NAME: str = Field(default="")

    # AI Models
    GOOGLE_API_KEY: str = Field(default="")
    GEMINI_EMBEDDING_MODEL: str = Field(default="", env="GEMINI_EMBEDDING_MODEL")
    GEMINI_MODEL_NAME: str = Field(default="", env="GEMINI_MODEL_NAME")

    # Vector Store
    VECTOR_COLLECTION_NAME: str = Field(
        default="knowflow_vecotr_db", env="VECTOR_COLLECTION_NAME"
    )
    CHUNK_SIZE: int = Field(default=700)
    CHUNK_OVERLAP: int = Field(default=80)
    TOP_K_RESULTS: int = Field(default=5)

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
        self._load_secrets()

    def _load_secrets(self):
        secrets = get_aws_secret("knowflow/app-secrets")

        if secrets:
            self.SECRET_KEY = secrets.get("SECRET_KEY", self.SECRET_KEY)
            self.ACCESS_TOKEN_EXPIRE_MINUTES = int(
                secrets.get(
                    "ACCESS_TOKEN_EXPIRE_MINUTES", self.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            )
            self.DATABASE_URL = secrets.get("DATABASE_URL", self.DATABASE_URL)
            self.NEO4J_URI = secrets.get("NEO4J_URI", self.NEO4J_URI)
            self.NEO4J_USER = secrets.get("NEO4J_USER", self.NEO4J_USER)
            self.NEO4J_PASSWORD = secrets.get("NEO4J_PASSWORD", self.NEO4J_PASSWORD)
            self.AWS_ACCESS_KEY_ID = secrets.get(
                "AWS_ACCESS_KEY_ID", self.AWS_ACCESS_KEY_ID
            )
            self.AWS_SECRET_ACCESS_KEY = secrets.get(
                "AWS_SECRET_ACCESS_KEY", self.AWS_SECRET_ACCESS_KEY
            )
            self.S3_BUCKET_NAME = secrets.get("S3_BUCKET_NAME", self.S3_BUCKET_NAME)
            self.GOOGLE_API_KEY = secrets.get("GOOGLE_API_KEY", self.GOOGLE_API_KEY)
            self.GEMINI_EMBEDDING_MODEL = secrets.get(
                "GEMINI_EMBEDDING_MODEL", self.GEMINI_EMBEDDING_MODEL
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
