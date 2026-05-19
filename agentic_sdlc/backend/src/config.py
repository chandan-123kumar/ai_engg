from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/agentic_workflow"
    kafka_bootstrap_servers: str = "localhost:9092"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 1440

    model_config = {"env_file": ".env"}

settings = Settings()
