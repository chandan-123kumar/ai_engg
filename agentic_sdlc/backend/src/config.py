from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5433/agentic_workflow"
    test_database_url: str = "postgresql://postgres:postgres@localhost:5433/agentic_workflow_test"
    kafka_bootstrap_servers: str = "localhost:9092"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 1440

    model_config = {"env_file": ".env"}

settings = Settings()
