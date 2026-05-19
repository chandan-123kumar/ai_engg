from fastapi import FastAPI
from src.health.router import router as health_router
from src.auth.router import router as auth_router
from src.workflows.router import router as workflow_router

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workflow_router)
