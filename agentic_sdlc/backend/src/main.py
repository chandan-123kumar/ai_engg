import asyncio
from fastapi import FastAPI
from src.health.router import router as health_router
from src.auth.router import router as auth_router
from src.workflows.router import router as workflow_router
from src.engine.router import router as engine_router
from src.state.router import router as state_router
from src.agents.registry.router import router as agent_registry_router
from src.websocket.router import router as ws_router
from src.websocket.manager import manager

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workflow_router)
app.include_router(engine_router)
app.include_router(state_router)
app.include_router(agent_registry_router)
app.include_router(ws_router)

@app.on_event("startup")
async def startup():
    manager.set_loop(asyncio.get_event_loop())
