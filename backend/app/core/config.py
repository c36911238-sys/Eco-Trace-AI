import os
import secrets
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "EcoTrace AI+"
    API_V1_STR: str = "/api/v1"

    # SECRET_KEY must be set via .env in production.
    # A secure random key is generated as a fallback ONLY for local dev.
    SECRET_KEY: str = secrets.token_urlsafe(32)

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    JWT_ALGORITHM: str = "HS256"

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Set DB_ECHO=True in your .env file to debug queries locally.
    DB_ECHO: bool = False

    # SQLite for local dev; swap to postgresql+asyncpg:// for production.
    SQLALCHEMY_DATABASE_URI: str = "sqlite+aiosqlite:///./ecotrace.db"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @model_validator(mode="after")
    def validate_and_adjust_settings(self) -> "Settings":
        # Allow a weak secret ONLY if explicitly running tests.
        is_testing = os.getenv("TESTING", "false").lower() == "true"
        if not is_testing and len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY is too short. Set a strong key (min 32 chars) in .env."
            )
        return self

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
    }


settings = Settings()
