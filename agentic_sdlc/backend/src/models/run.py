import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from src.database import Base

class RunStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"
    halted = "halted"

class ExecutionStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    escalated = "escalated"

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    current_stage_id = Column(UUID(as_uuid=True), ForeignKey("stages.id"), nullable=True)
    trigger_payload = Column(JSONB, nullable=False, default=dict)
    status = Column(String, nullable=False, default=RunStatus.running)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class StageExecution(Base):
    __tablename__ = "stage_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("stages.id"), nullable=False)
    executor_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default=ExecutionStatus.pending)
    result = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SubStepExecution(Base):
    __tablename__ = "sub_step_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_execution_id = Column(UUID(as_uuid=True), ForeignKey("stage_executions.id"), nullable=False)
    sub_step_id = Column(UUID(as_uuid=True), ForeignKey("sub_steps.id"), nullable=False)
    status = Column(String, nullable=False, default=ExecutionStatus.pending)
    result = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
