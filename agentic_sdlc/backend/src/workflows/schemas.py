from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class WorkflowCreate(BaseModel):
    name: str
    trigger: dict = {}

class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    status: str
    version: str
    trigger: dict

    model_config = {"from_attributes": True}

class StageCreate(BaseModel):
    name: str
    order: int
    executor_type: str
    gate_type: Optional[str] = None
    config: dict = {}

class StageResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    name: str
    order: int
    executor_type: str
    gate_type: Optional[str] = None

    model_config = {"from_attributes": True}

class SubStepCreate(BaseModel):
    name: str
    order: int
    executor_type: str
    agent_conversation_config: Optional[dict] = None
    on_complete: Optional[str] = None
    on_reject: Optional[str] = None

class SubStepResponse(BaseModel):
    id: UUID
    stage_id: UUID
    name: str
    order: int
    executor_type: str
    agent_conversation_config: Optional[dict] = None

    model_config = {"from_attributes": True}
