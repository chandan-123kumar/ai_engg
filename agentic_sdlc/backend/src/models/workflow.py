import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from src.database import Base

class WorkflowStatus(str, enum.Enum):
    draft = "draft"
    active = "active"

class ExecutorType(str, enum.Enum):
    agent = "agent"
    human = "human"

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False, default="1")
    config = Column(JSONB, nullable=False, default=dict)
    status = Column(Enum(WorkflowStatus), nullable=False, default=WorkflowStatus.draft)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Stage(Base):
    __tablename__ = "stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    executor_type = Column(Enum(ExecutorType), nullable=False)
    gate_type = Column(String, nullable=True)
    config = Column(JSONB, nullable=False, default=dict)

class SubStep(Base):
    __tablename__ = "sub_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("stages.id"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    executor_type = Column(Enum(ExecutorType), nullable=False)
    agent_conversation_config = Column(JSONB, nullable=True)
    on_complete = Column(String, nullable=True)
    on_reject = Column(String, nullable=True)
