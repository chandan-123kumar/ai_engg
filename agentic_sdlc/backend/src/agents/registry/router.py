from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.agents.registry import service
from src.agents.registry.schemas import (
    AgentRegistryCreate, AgentRegistryUpdate, AgentRegistryResponse
)

router = APIRouter(prefix="/agents/registry")


@router.post("", status_code=201, response_model=AgentRegistryResponse)
def register_agent(body: AgentRegistryCreate, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    if service.get_agent(db, body.agent_type):
        raise HTTPException(status_code=409, detail="Agent type already registered")
    return service.create_agent(
        db, body.agent_type, body.name, body.description,
        body.input_schema, body.output_schema, body.endpoint,
        body.provider, body.provider_config,
    )


@router.get("", response_model=list[AgentRegistryResponse])
def list_agents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_agents(db)


@router.get("/{agent_type}", response_model=AgentRegistryResponse)
def get_agent(agent_type: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    agent = service.get_agent(db, agent_type)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_type}", response_model=AgentRegistryResponse)
def update_agent(agent_type: str, body: AgentRegistryUpdate,
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    agent = service.update_agent(
        db, agent_type,
        name=body.name, description=body.description,
        provider=body.provider, provider_config=body.provider_config,
        endpoint=body.endpoint,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
