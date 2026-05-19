# Agentic Workflow Platform — Plan 1: Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the project skeleton — Docker infra (Postgres + Kafka), full Postgres schema, FastAPI app with basic auth (register/login/JWT), and a health endpoint. All subsequent plans build on this.

**Architecture:** Monorepo with `agentic_sdlc/backend/` (FastAPI + SQLAlchemy) and `agentic_sdlc/infra/` (Docker Compose). Auth uses bcrypt password hashing and signed JWT stored in httpOnly cookie. Kafka and Postgres run locally via Docker Compose.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Postgres 15, Kafka (Confluent), bcrypt, PyJWT, pytest, httpx

---

## File Map

```
agentic_sdlc/
  docker-compose.yml                   ← Postgres + Zookeeper + Kafka
  backend/
    pyproject.toml                     ← deps + dev deps
    .env.example                       ← env var template
    alembic.ini                        ← alembic config
    alembic/
      env.py                           ← alembic runtime config
      versions/
        001_initial_schema.py          ← full schema migration
    src/
      __init__.py
      main.py                          ← FastAPI app factory, router registration
      config.py                        ← pydantic-settings config
      database.py                      ← engine, session, Base, get_db
      models/
        __init__.py
        user.py                        ← User table
        workflow.py                    ← Workflow + Stage + SubStep tables
        run.py                         ← WorkflowRun + StageExecution + SubStepExecution
        task.py                        ← AgentTask + HumanTask + AgentConversation
        agent_registry.py              ← AgentRegistry table
      auth/
        __init__.py
        router.py                      ← POST /auth/register, POST /auth/login
        service.py                     ← hash_password, verify_password, create_token, decode_token
        dependencies.py                ← get_current_user FastAPI dependency
      health/
        __init__.py
        router.py                      ← GET /health
    tests/
      __init__.py
      conftest.py                      ← test db, test client fixtures
      test_health.py
      test_auth.py
```

---

## Task 1: Project Scaffold + Docker Compose

**Files:**
- Create: `agentic_sdlc/docker-compose.yml`
- Create: `agentic_sdlc/backend/pyproject.toml`
- Create: `agentic_sdlc/backend/.env.example`

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p agentic_sdlc/backend/src/models
mkdir -p agentic_sdlc/backend/src/auth
mkdir -p agentic_sdlc/backend/src/health
mkdir -p agentic_sdlc/backend/alembic/versions
mkdir -p agentic_sdlc/backend/tests
touch agentic_sdlc/backend/src/__init__.py
touch agentic_sdlc/backend/src/models/__init__.py
touch agentic_sdlc/backend/src/auth/__init__.py
touch agentic_sdlc/backend/src/health/__init__.py
touch agentic_sdlc/backend/tests/__init__.py
```

- [ ] **Step 2: Write docker-compose.yml**

`agentic_sdlc/docker-compose.yml`:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: agentic_workflow
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"

volumes:
  pgdata:
```

- [ ] **Step 3: Write pyproject.toml**

`agentic_sdlc/backend/pyproject.toml`:
```toml
[project]
name = "agentic-workflow-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.111.0",
  "uvicorn[standard]>=0.30.0",
  "sqlalchemy>=2.0.0",
  "alembic>=1.13.0",
  "psycopg2-binary>=2.9.0",
  "kafka-python>=2.0.2",
  "bcrypt>=4.1.0",
  "pyjwt>=2.8.0",
  "python-dotenv>=1.0.0",
  "pydantic-settings>=2.3.0",
  "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "httpx>=0.27.0",
  "pytest-asyncio>=0.23.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 4: Write .env.example**

`agentic_sdlc/backend/.env.example`:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentic_workflow
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
JWT_SECRET=change-me-in-production
JWT_EXPIRE_MINUTES=1440
```

Copy to `.env`:
```bash
cp agentic_sdlc/backend/.env.example agentic_sdlc/backend/.env
```

- [ ] **Step 5: Install dependencies**

```bash
cd agentic_sdlc/backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: all packages install without error.

- [ ] **Step 6: Start infra**

```bash
cd agentic_sdlc
docker compose up -d
docker compose ps
```

Expected: `postgres` and `kafka` and `zookeeper` show `running`.

- [ ] **Step 7: Commit**

```bash
git add agentic_sdlc/
git commit -m "feat: scaffold agentic_sdlc project with docker compose infra"
```

---

## Task 2: Config + Database Connection

**Files:**
- Create: `agentic_sdlc/backend/src/config.py`
- Create: `agentic_sdlc/backend/src/database.py`

- [ ] **Step 1: Write config.py**

`agentic_sdlc/backend/src/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/agentic_workflow"
    kafka_bootstrap_servers: str = "localhost:9092"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 1440

    model_config = {"env_file": ".env"}

settings = Settings()
```

- [ ] **Step 2: Write database.py**

`agentic_sdlc/backend/src/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from src.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Verify connection**

```bash
cd agentic_sdlc/backend
python -c "from src.database import engine; conn = engine.connect(); conn.close(); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add agentic_sdlc/backend/src/config.py agentic_sdlc/backend/src/database.py
git commit -m "feat: add config and database connection"
```

---

## Task 3: SQLAlchemy Models

**Files:**
- Create: `agentic_sdlc/backend/src/models/user.py`
- Create: `agentic_sdlc/backend/src/models/workflow.py`
- Create: `agentic_sdlc/backend/src/models/run.py`
- Create: `agentic_sdlc/backend/src/models/task.py`
- Create: `agentic_sdlc/backend/src/models/agent_registry.py`
- Modify: `agentic_sdlc/backend/src/models/__init__.py`

- [ ] **Step 1: Write user.py**

`agentic_sdlc/backend/src/models/user.py`:
```python
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: Write workflow.py**

`agentic_sdlc/backend/src/models/workflow.py`:
```python
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
```

- [ ] **Step 3: Write run.py**

`agentic_sdlc/backend/src/models/run.py`:
```python
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
```

- [ ] **Step 4: Write task.py**

`agentic_sdlc/backend/src/models/task.py`:
```python
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
```

- [ ] **Step 5: Write agent_registry.py**

`agentic_sdlc/backend/src/models/agent_registry.py`:
```python
import uuid
import enum
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from src.database import Base

class ProviderType(str, enum.Enum):
    claude_cli = "claude_cli"
    claude_api = "claude_api"

class AgentRegistry(Base):
    __tablename__ = "agent_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    input_schema = Column(JSONB, nullable=False, default=dict)
    output_schema = Column(JSONB, nullable=False, default=dict)
    endpoint = Column(String, nullable=True)
    provider = Column(String, nullable=False, default=ProviderType.claude_cli)
    provider_config = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 6: Update models/__init__.py to export all models**

`agentic_sdlc/backend/src/models/__init__.py`:
```python
from src.models.user import User
from src.models.workflow import Workflow, Stage, SubStep, WorkflowStatus, ExecutorType
from src.models.run import WorkflowRun, StageExecution, SubStepExecution, RunStatus, ExecutionStatus
from src.models.task import AgentTask, HumanTask, AgentConversation, TaskStatus, HumanTaskStatus
from src.models.agent_registry import AgentRegistry, ProviderType
```

- [ ] **Step 7: Verify models import cleanly**

```bash
cd agentic_sdlc/backend
python -c "from src.models import User, Workflow, WorkflowRun, AgentTask; print('OK')"
```

Expected: `OK`

- [ ] **Step 8: Commit**

```bash
git add agentic_sdlc/backend/src/models/
git commit -m "feat: add all sqlalchemy models"
```

---

## Task 4: Alembic Migration

**Files:**
- Create: `agentic_sdlc/backend/alembic.ini`
- Create: `agentic_sdlc/backend/alembic/env.py`
- Create: `agentic_sdlc/backend/alembic/versions/001_initial_schema.py`

- [ ] **Step 1: Initialise alembic**

```bash
cd agentic_sdlc/backend
alembic init alembic
```

- [ ] **Step 2: Update alembic.ini — set sqlalchemy.url**

In `alembic.ini`, find the line:
```
sqlalchemy.url = driver://user:pass@localhost/dbname
```
Replace with:
```
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/agentic_workflow
```

- [ ] **Step 3: Update alembic/env.py — import models so autogenerate sees them**

Replace the contents of `agentic_sdlc/backend/alembic/env.py`:
```python
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database import Base
import src.models  # noqa: F401 — registers all models with Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Autogenerate the migration**

```bash
cd agentic_sdlc/backend
alembic revision --autogenerate -m "initial schema"
```

Expected: creates `alembic/versions/xxxx_initial_schema.py` with all table definitions.

- [ ] **Step 5: Run the migration**

```bash
alembic upgrade head
```

Expected: output shows each table being created, ends with `Done.`

- [ ] **Step 6: Verify tables exist**

```bash
python -c "
from src.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print(inspector.get_table_names())
"
```

Expected output includes: `['agent_conversations', 'agent_registry', 'agent_tasks', 'human_tasks', 'stages', 'sub_step_executions', 'sub_steps', 'stage_executions', 'users', 'workflow_runs', 'workflows']`

- [ ] **Step 7: Commit**

```bash
git add agentic_sdlc/backend/alembic/
git add agentic_sdlc/backend/alembic.ini
git commit -m "feat: add alembic migration for initial schema"
```

---

## Task 5: Health Endpoint (TDD)

**Files:**
- Create: `agentic_sdlc/backend/src/health/router.py`
- Create: `agentic_sdlc/backend/tests/conftest.py`
- Create: `agentic_sdlc/backend/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

`agentic_sdlc/backend/tests/conftest.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

`agentic_sdlc/backend/tests/test_health.py`:
```python
import pytest

@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd agentic_sdlc/backend
pytest tests/test_health.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.main'`

- [ ] **Step 3: Write the health router**

`agentic_sdlc/backend/src/health/router.py`:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Write the FastAPI app**

`agentic_sdlc/backend/src/main.py`:
```python
from fastapi import FastAPI
from src.health.router import router as health_router

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
```

- [ ] **Step 5: Run test — verify it passes**

```bash
pytest tests/test_health.py -v
```

Expected: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add agentic_sdlc/backend/src/health/ agentic_sdlc/backend/src/main.py agentic_sdlc/backend/tests/
git commit -m "feat: add health endpoint with tests"
```

---

## Task 6: Auth Service (TDD)

**Files:**
- Create: `agentic_sdlc/backend/src/auth/service.py`
- Create: `agentic_sdlc/backend/tests/test_auth.py` (service tests first)

- [ ] **Step 1: Write failing tests for auth service**

`agentic_sdlc/backend/tests/test_auth.py`:
```python
import pytest
from src.auth.service import hash_password, verify_password, create_token, decode_token

def test_hash_password_returns_different_string():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert len(hashed) > 20

def test_verify_password_correct():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True

def test_verify_password_wrong():
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False

def test_create_and_decode_token():
    token = create_token(user_id="abc-123", email="test@example.com")
    payload = decode_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["email"] == "test@example.com"

def test_decode_invalid_token_raises():
    with pytest.raises(Exception):
        decode_token("not.a.valid.token")
```

- [ ] **Step 2: Run — verify fails**

```bash
pytest tests/test_auth.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.auth.service'`

- [ ] **Step 3: Write auth service**

`agentic_sdlc/backend/src/auth/service.py`:
```python
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from src.config import settings

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
```

- [ ] **Step 4: Run — verify passes**

```bash
pytest tests/test_auth.py -v -k "not router"
```

Expected: all 5 service tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add agentic_sdlc/backend/src/auth/service.py agentic_sdlc/backend/tests/test_auth.py
git commit -m "feat: add auth service with password hashing and JWT"
```

---

## Task 7: Auth Router — Register + Login (TDD)

**Files:**
- Create: `agentic_sdlc/backend/src/auth/router.py`
- Create: `agentic_sdlc/backend/src/auth/dependencies.py`
- Modify: `agentic_sdlc/backend/src/main.py`
- Modify: `agentic_sdlc/backend/tests/test_auth.py`

- [ ] **Step 1: Add router tests to test_auth.py**

Append to `agentic_sdlc/backend/tests/test_auth.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.database import Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_register_creates_user(client):
    response = await client.post("/auth/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "strongpass123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "password_hash" not in data

@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client):
    payload = {"name": "Alice", "email": "alice@example.com", "password": "pass"}
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_login_returns_token(client):
    await client.post("/auth/register", json={
        "name": "Alice", "email": "alice@example.com", "password": "pass123"
    })
    response = await client.post("/auth/login", json={
        "email": "alice@example.com", "password": "pass123"
    })
    assert response.status_code == 200
    assert "token" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password_fails(client):
    await client.post("/auth/register", json={
        "name": "Alice", "email": "alice@example.com", "password": "pass123"
    })
    response = await client.post("/auth/login", json={
        "email": "alice@example.com", "password": "wrong"
    })
    assert response.status_code == 401
```

- [ ] **Step 2: Run — verify fails**

```bash
pytest tests/test_auth.py -v -k "router or register or login"
```

Expected: FAIL — router not yet defined.

- [ ] **Step 3: Write auth router**

`agentic_sdlc/backend/src/auth/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User
from src.auth.service import hash_password, verify_password, create_token
import uuid

router = APIRouter(prefix="/auth")

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        id=uuid.uuid4(),
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "name": user.name, "email": user.email}

@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user_id=str(user.id), email=user.email)
    return {"token": token}
```

- [ ] **Step 4: Write auth dependency**

`agentic_sdlc/backend/src/auth/dependencies.py`:
```python
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User
from src.auth.service import decode_token
import jwt

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError
        payload = decode_token(token)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise ValueError
        return user
    except (jwt.PyJWTError, ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

- [ ] **Step 5: Register auth router in main.py**

`agentic_sdlc/backend/src/main.py`:
```python
from fastapi import FastAPI
from src.health.router import router as health_router
from src.auth.router import router as auth_router

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
app.include_router(auth_router)
```

- [ ] **Step 6: Run all tests — verify pass**

```bash
pytest tests/ -v
```

Expected: all tests `PASSED`

- [ ] **Step 7: Commit**

```bash
git add agentic_sdlc/backend/src/auth/ agentic_sdlc/backend/src/main.py agentic_sdlc/backend/tests/test_auth.py
git commit -m "feat: add auth register and login endpoints with JWT"
```

---

## Task 8: Smoke Test — Run the Server

- [ ] **Step 1: Start the server**

```bash
cd agentic_sdlc/backend
uvicorn src.main:app --reload
```

Expected: `Uvicorn running on http://127.0.0.1:8000`

- [ ] **Step 2: Hit health endpoint**

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 3: Register a user**

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"pass123"}'
```

Expected: `{"id":"...","name":"Test User","email":"test@example.com"}`

- [ ] **Step 4: Login and get token**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
```

Expected: `{"token":"eyJ..."}`

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: plan 1 foundation complete — infra, schema, auth, health"
```

---

## Summary

After Plan 1 you have:
- Self-hosted Kafka + Postgres running via Docker Compose
- Full Postgres schema for workflows, runs, tasks, agent registry
- FastAPI app with `/health` and `/auth/register` + `/auth/login`
- JWT-based auth dependency ready for all future routes
- All tests passing

**Next:** Plan 2 — Workflow Engine + Kafka routing (CRUD for workflows/stages/sub-steps, engine that reads definitions and dispatches tasks to Kafka topics).
