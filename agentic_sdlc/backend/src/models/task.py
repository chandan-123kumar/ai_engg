import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from src.database import Base

class TaskStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"

class HumanTaskStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class ConversationStatus(str, enum.Enum):
    pending = "pending"
    complete = "complete"
    escalated = "escalated"

class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub_step_execution_id = Column(UUID(as_uuid=True), ForeignKey("sub_step_executions.id"), nullable=False)
    agent_type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    status = Column(String, nullable=False, default=TaskStatus.queued)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class HumanTask(Base):
    __tablename__ = "human_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub_step_execution_id = Column(UUID(as_uuid=True), ForeignKey("sub_step_executions.id"), nullable=False)
    gate_type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    status = Column(String, nullable=False, default=HumanTaskStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub_step_execution_id = Column(UUID(as_uuid=True), ForeignKey("sub_step_executions.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    from_agent = Column(String, nullable=False)
    to_agent = Column(String, nullable=False)
    message = Column(JSONB, nullable=False, default=dict)
    status = Column(String, nullable=False, default=ConversationStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
