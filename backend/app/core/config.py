from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Travel AI Platform"
    PROJECT_VERSION: str = "0.1.0"

    # Database
    DATABASE_URL: str = "postgresql://dev:dev123@localhost:5432/travel_ai"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # OpenAI (или OpenAI-совместимый провайдер, например Google Gemini)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # MinIO
    MINIO_URL: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()