import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Automated IT Ticket Classification System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "supersecret_insecure_key_change_in_production_jwt_secret_token"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./helpdesk.db"

    # ML & Artifacts
    MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "artifacts")
    CONFIDENCE_THRESHOLD: float = 0.80

    # Uploads
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_MIME_TYPES: List[str] = [
        "image/png",
        "image/jpeg",
        "image/webp",
        "application/pdf",
        "text/plain",
        "application/zip",
        "application/x-zip-compressed",
    ]

    # SLA Rules in Hours
    SLA_HOURS: dict = {
        "CRITICAL": 2,
        "HIGH": 4,
        "MEDIUM": 24,
        "LOW": 72,
    }

    # Department mapping
    CATEGORY_DEPARTMENT_MAP: dict = {
        "Network": "Network Support",
        "Hardware": "Hardware Support",
        "Software": "Software Support",
        "Email": "Email Support",
        "Security": "Security",
        "Account & Access": "IT Helpdesk",
        "Server / Infrastructure": "Infrastructure",
    }

    CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
