from fastapi import FastAPI
from src.health.router import router as health_router

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
