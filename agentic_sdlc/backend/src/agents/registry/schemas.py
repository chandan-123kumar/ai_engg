from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class AgentRegistryCreate(BaseModel):
    agent_type: str
    name: str
    description: Optional[str] = None
    input_schema: dict = {}
    output_schema: dict = {}
    endpoint: Optional[str] = None
    provider: str = "claude_cli"
    provider_config: dict = {}


class AgentRegistryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    provider_config: Optional[dict] = None
    endpoint: Optional[str] = None


class AgentRegistryResponse(BaseModel):
    id: UUID
    agent_type: str
    name: str
    description: Optional[str] = None
    provider: str
    provider_config: dict
    endpoint: Optional[str] = None

    model_config = {"from_attributes": True}
