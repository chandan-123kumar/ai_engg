# Agentic Workflow Platform — Plan 3: Agent Workers + Conversation Loops

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Agent Registry CRUD API, pluggable agent workers that consume from `agent.tasks` Kafka topic, two LLM providers (Claude CLI subprocess and Claude API via Anthropic SDK), and the ConversationLoop that drives back-and-forth between agents within a sub-step until a termination condition is met.

**Architecture:** Agent workers are Kafka consumers. Each worker reads an agent task, looks up the agent type in the registry, selects the configured provider (claude_cli or claude_api), calls the LLM, and publishes results to `agent.results`. The ConversationLoop runs within a sub-step execution, orchestrating multi-turn exchanges between two agents and evaluating termination conditions (single_turn, reviewer_approves, max_turns, tool_success). Also fixes the test DB isolation issue from Plan 2.

**Tech Stack:** FastAPI, SQLAlchemy, kafka-python, anthropic SDK, subprocess (for Claude CLI), pytest with test DB isolation

---

## File Map

```
agentic_sdlc/backend/
  src/
    agents/
      __init__.py
      registry/
        __init__.py
        schemas.py       ← Pydantic request/response schemas
        service.py       ← DB ops: create/get/list/update agent registry entries
        router.py        ← CRUD routes: /agents/registry
      worker/
        __init__.py
        base.py          ← AgentWorker: consumes agent.tasks, dispatches to provider
        claude_cli.py    ← ClaudeCliProvider: calls `claude -p` subprocess
        claude_api.py    ← ClaudeApiProvider: calls Anthropic SDK
      conversation/
        __init__.py
        loop.py          ← ConversationLoop: multi-turn agent exchange + termination
  tests/
    test_agent_registry.py
    test_agent_worker.py
    test_conversation_loop.py
```

---

## Task 1: Fix Test DB Isolation

Tests currently share the main DB and `drop_all` in teardown wipes the schema. Fix: add a `TEST_DATABASE_URL` pointing to a separate `agentic_workflow_test` DB, and use it only in tests.

**Files:**
- Modify: `agentic_sdlc/backend/src/config.py`
- Modify: `agentic_sdlc/backend/tests/conftest.py`

- [ ] **Step 1: Add test DB URL to config**

`agentic_sdlc/backend/src/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5433/agentic_workflow"
    test_database_url: str = "postgresql://postgres:postgres@localhost:5433/agentic_workflow_test"
    kafka_bootstrap_servers: str = "localhost:9092"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 1440

    model_config = {"env_file": ".env"}

settings = Settings()
```

- [ ] **Step 2: Create the test database**

```bash
cd agentic_sdlc/backend
source .venv/bin/activate
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/postgres')
conn.autocommit = True
cur = conn.cursor()
cur.execute('CREATE DATABASE agentic_workflow_test')
conn.close()
print('test DB created')
"
```

Expected: `test DB created`

- [ ] **Step 3: Update conftest.py to use test DB**

`agentic_sdlc/backend/tests/conftest.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.database import Base, get_db
from src.config import settings

test_engine = create_engine(settings.test_database_url)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

- [ ] **Step 4: Run full test suite — verify still passing**

```bash
cd agentic_sdlc/backend
source .venv/bin/activate
pytest tests/ -v 2>&1 | tail -8
```

Expected: `22 passed`

- [ ] **Step 5: Verify main DB schema still intact**

```bash
python -c "
from src.database import engine
from sqlalchemy import inspect
print('Main DB tables:', len(inspect(engine).get_table_names()))
"
```

Expected: `Main DB tables: 12`

- [ ] **Step 6: Commit**

```bash
git add agentic_sdlc/backend/src/config.py agentic_sdlc/backend/tests/conftest.py
git commit -m "fix: isolate tests to dedicated test database"
```

---

## Task 2: Agent Registry CRUD API (TDD)

**Files:**
- Create: `agentic_sdlc/backend/src/agents/__init__.py`
- Create: `agentic_sdlc/backend/src/agents/registry/__init__.py`
- Create: `agentic_sdlc/backend/src/agents/registry/schemas.py`
- Create: `agentic_sdlc/backend/src/agents/registry/service.py`
- Create: `agentic_sdlc/backend/src/agents/registry/router.py`
- Create: `agentic_sdlc/backend/tests/test_agent_registry.py`
- Modify: `agentic_sdlc/backend/src/main.py`

- [ ] **Step 1: Write failing tests**

`agentic_sdlc/backend/tests/test_agent_registry.py`:
```python
import pytest


async def _auth(client):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_register_agent(client, setup_db):
    headers = await _auth(client)
    response = await client.post("/agents/registry", json={
        "agent_type": "coder",
        "name": "Code Generator",
        "description": "Writes code based on spec",
        "input_schema": {"spec": "string"},
        "output_schema": {"code": "string"},
        "provider": "claude_api",
        "provider_config": {"model": "claude-sonnet-4-6"}
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["agent_type"] == "coder"
    assert data["provider"] == "claude_api"


@pytest.mark.asyncio
async def test_list_agents(client, setup_db):
    headers = await _auth(client)
    await client.post("/agents/registry", json={
        "agent_type": "coder", "name": "Coder", "input_schema": {},
        "output_schema": {}, "provider": "claude_cli", "provider_config": {}
    }, headers=headers)
    await client.post("/agents/registry", json={
        "agent_type": "reviewer", "name": "Reviewer", "input_schema": {},
        "output_schema": {}, "provider": "claude_api", "provider_config": {}
    }, headers=headers)
    response = await client.get("/agents/registry", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_agent_by_type(client, setup_db):
    headers = await _auth(client)
    await client.post("/agents/registry", json={
        "agent_type": "planner", "name": "Planner", "input_schema": {},
        "output_schema": {}, "provider": "claude_api",
        "provider_config": {"model": "claude-sonnet-4-6"}
    }, headers=headers)
    response = await client.get("/agents/registry/planner", headers=headers)
    assert response.status_code == 200
    assert response.json()["agent_type"] == "planner"


@pytest.mark.asyncio
async def test_update_agent_provider(client, setup_db):
    headers = await _auth(client)
    await client.post("/agents/registry", json={
        "agent_type": "coder", "name": "Coder", "input_schema": {},
        "output_schema": {}, "provider": "claude_cli", "provider_config": {}
    }, headers=headers)
    response = await client.patch("/agents/registry/coder", json={
        "provider": "claude_api",
        "provider_config": {"model": "claude-opus-4-7", "api_key": "sk-test"}
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["provider"] == "claude_api"


@pytest.mark.asyncio
async def test_duplicate_agent_type_fails(client, setup_db):
    headers = await _auth(client)
    payload = {"agent_type": "coder", "name": "Coder", "input_schema": {},
               "output_schema": {}, "provider": "claude_cli", "provider_config": {}}
    await client.post("/agents/registry", json=payload, headers=headers)
    response = await client.post("/agents/registry", json=payload, headers=headers)
    assert response.status_code == 409
```

- [ ] **Step 2: Run — verify fails**

```bash
pytest tests/test_agent_registry.py -v 2>&1 | tail -5
```

Expected: FAIL — `404` (routes not yet registered)

- [ ] **Step 3: Write schemas.py**

`agentic_sdlc/backend/src/agents/registry/schemas.py`:
```python
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
```

- [ ] **Step 4: Write service.py**

`agentic_sdlc/backend/src/agents/registry/service.py`:
```python
import uuid
from sqlalchemy.orm import Session
from src.models.agent_registry import AgentRegistry

def create_agent(db: Session, agent_type: str, name: str, description: str | None,
                 input_schema: dict, output_schema: dict, endpoint: str | None,
                 provider: str, provider_config: dict) -> AgentRegistry:
    agent = AgentRegistry(
        id=uuid.uuid4(), agent_type=agent_type, name=name,
        description=description, input_schema=input_schema,
        output_schema=output_schema, endpoint=endpoint,
        provider=provider, provider_config=provider_config,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

def list_agents(db: Session) -> list[AgentRegistry]:
    return db.query(AgentRegistry).all()

def get_agent(db: Session, agent_type: str) -> AgentRegistry | None:
    return db.query(AgentRegistry).filter(AgentRegistry.agent_type == agent_type).first()

def update_agent(db: Session, agent_type: str, **kwargs) -> AgentRegistry | None:
    agent = get_agent(db, agent_type)
    if not agent:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(agent, key, value)
    db.commit()
    db.refresh(agent)
    return agent
```

- [ ] **Step 5: Write router.py**

`agentic_sdlc/backend/src/agents/registry/router.py`:
```python
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
```

- [ ] **Step 6: Create __init__.py files**

```bash
mkdir -p agentic_sdlc/backend/src/agents/registry
mkdir -p agentic_sdlc/backend/src/agents/worker
mkdir -p agentic_sdlc/backend/src/agents/conversation
touch agentic_sdlc/backend/src/agents/__init__.py
touch agentic_sdlc/backend/src/agents/registry/__init__.py
touch agentic_sdlc/backend/src/agents/worker/__init__.py
touch agentic_sdlc/backend/src/agents/conversation/__init__.py
```

- [ ] **Step 7: Register router in main.py**

`agentic_sdlc/backend/src/main.py`:
```python
from fastapi import FastAPI
from src.health.router import router as health_router
from src.auth.router import router as auth_router
from src.workflows.router import router as workflow_router
from src.engine.router import router as engine_router
from src.state.router import router as state_router
from src.agents.registry.router import router as agent_registry_router

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workflow_router)
app.include_router(engine_router)
app.include_router(state_router)
app.include_router(agent_registry_router)
```

- [ ] **Step 8: Run tests — verify pass**

```bash
pytest tests/test_agent_registry.py -v 2>&1 | tail -8
```

Expected: `5 passed`

- [ ] **Step 9: Commit**

```bash
git add agentic_sdlc/backend/src/agents/ agentic_sdlc/backend/src/main.py agentic_sdlc/backend/tests/test_agent_registry.py
git commit -m "feat: add agent registry CRUD API"
```

---

## Task 3: LLM Providers — Claude CLI + Claude API

**Files:**
- Create: `agentic_sdlc/backend/src/agents/worker/claude_cli.py`
- Create: `agentic_sdlc/backend/src/agents/worker/claude_api.py`
- Modify: `agentic_sdlc/backend/pyproject.toml` (add anthropic)
- Create: `agentic_sdlc/backend/tests/test_agent_worker.py`

- [ ] **Step 1: Add anthropic to dependencies**

`agentic_sdlc/backend/pyproject.toml` — add to `dependencies`:
```toml
  "anthropic>=0.40.0",
```

Install:
```bash
cd agentic_sdlc/backend
source .venv/bin/activate
pip install anthropic -q && echo "installed"
```

Expected: `installed`

- [ ] **Step 2: Write failing tests for providers**

`agentic_sdlc/backend/tests/test_agent_worker.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from src.agents.worker.claude_cli import ClaudeCliProvider
from src.agents.worker.claude_api import ClaudeApiProvider

# --- Claude CLI Provider ---

def test_claude_cli_returns_text():
    provider = ClaudeCliProvider(cli_path="claude", model="claude-sonnet-4-6")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"result": "here is the code"}',
            stderr=""
        )
        result = provider.call(
            system_prompt="You are a coder.",
            user_message="Write a hello world function."
        )
    assert isinstance(result, str)
    assert len(result) > 0

def test_claude_cli_raises_on_nonzero_exit():
    provider = ClaudeCliProvider(cli_path="claude", model="claude-sonnet-4-6")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        with pytest.raises(RuntimeError, match="Claude CLI error"):
            provider.call(system_prompt="You are a coder.", user_message="Write code.")

# --- Claude API Provider ---

def test_claude_api_returns_text():
    provider = ClaudeApiProvider(api_key="sk-test", model="claude-sonnet-4-6")
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="def hello(): return 'world'")]
    with patch("anthropic.Anthropic") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        result = provider.call(
            system_prompt="You are a coder.",
            user_message="Write a hello world function."
        )
    assert result == "def hello(): return 'world'"

def test_claude_api_passes_correct_model():
    provider = ClaudeApiProvider(api_key="sk-test", model="claude-opus-4-7")
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="output")]
    with patch("anthropic.Anthropic") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        provider.call(system_prompt="sys", user_message="msg")
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-opus-4-7"
```

- [ ] **Step 3: Run — verify fails**

```bash
pytest tests/test_agent_worker.py -v 2>&1 | tail -5
```

Expected: FAIL — modules not found.

- [ ] **Step 4: Write claude_cli.py**

`agentic_sdlc/backend/src/agents/worker/claude_cli.py`:
```python
import subprocess
import json

class ClaudeCliProvider:
    def __init__(self, cli_path: str = "claude", model: str = "claude-sonnet-4-6"):
        self.cli_path = cli_path
        self.model = model

    def call(self, system_prompt: str, user_message: str) -> str:
        full_prompt = f"{system_prompt}\n\n{user_message}"
        result = subprocess.run(
            [self.cli_path, "-p", full_prompt, "--model", self.model],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr}")
        output = result.stdout.strip()
        try:
            parsed = json.loads(output)
            return parsed.get("result", output)
        except json.JSONDecodeError:
            return output
```

- [ ] **Step 5: Write claude_api.py**

`agentic_sdlc/backend/src/agents/worker/claude_api.py`:
```python
import anthropic

class ClaudeApiProvider:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def call(self, system_prompt: str, user_message: str) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=8096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text
```

- [ ] **Step 6: Run tests — verify pass**

```bash
pytest tests/test_agent_worker.py -v 2>&1 | tail -8
```

Expected: `4 passed`

- [ ] **Step 7: Commit**

```bash
git add agentic_sdlc/backend/src/agents/worker/ agentic_sdlc/backend/pyproject.toml agentic_sdlc/backend/tests/test_agent_worker.py
git commit -m "feat: add claude cli and claude api providers"
```

---

## Task 4: Agent Worker (Kafka Consumer)

**Files:**
- Create: `agentic_sdlc/backend/src/agents/worker/base.py`

- [ ] **Step 1: Write base.py**

`agentic_sdlc/backend/src/agents/worker/base.py`:
```python
from src.kafka.consumer import BaseConsumer
from src.kafka.producer import publish
from src.kafka import topics
from src.database import SessionLocal
from src.models.agent_registry import AgentRegistry
from src.models.task import AgentTask, TaskStatus
from src.agents.worker.claude_cli import ClaudeCliProvider
from src.agents.worker.claude_api import ClaudeApiProvider

class AgentWorker(BaseConsumer):
    topic = topics.AGENT_TASKS

    def _get_provider(self, agent: AgentRegistry):
        cfg = agent.provider_config or {}
        if agent.provider == "claude_cli":
            return ClaudeCliProvider(
                cli_path=cfg.get("cli_path", "claude"),
                model=cfg.get("model", "claude-sonnet-4-6"),
            )
        if agent.provider == "claude_api":
            return ClaudeApiProvider(
                api_key=cfg.get("api_key", ""),
                model=cfg.get("model", "claude-sonnet-4-6"),
            )
        raise ValueError(f"Unknown provider: {agent.provider}")

    def handle(self, message: dict):
        db = SessionLocal()
        try:
            agent_type = message.get("agent_type")
            run_id = message.get("run_id")
            stage_execution_id = message.get("stage_execution_id")
            payload = message.get("payload", {})

            agent = db.query(AgentRegistry).filter(
                AgentRegistry.agent_type == agent_type
            ).first()
            if not agent:
                self._publish_failure(run_id, stage_execution_id, f"Unknown agent type: {agent_type}")
                return

            provider = self._get_provider(agent)
            system_prompt = payload.get("system_prompt", f"You are a {agent_type} agent.")
            user_message = payload.get("user_message", "")

            output = provider.call(system_prompt=system_prompt, user_message=user_message)

            publish(topics.AGENT_RESULTS, {
                "run_id": run_id,
                "stage_execution_id": stage_execution_id,
                "agent_type": agent_type,
                "output": output,
                "status": "done",
            }, key=run_id)

        except Exception as e:
            self._publish_failure(run_id, stage_execution_id, str(e))
        finally:
            db.close()

    def _publish_failure(self, run_id: str, stage_execution_id: str, error: str):
        publish(topics.AGENT_RESULTS, {
            "run_id": run_id,
            "stage_execution_id": stage_execution_id,
            "status": "failed",
            "error": error,
        }, key=run_id)
```

- [ ] **Step 2: Verify import**

```bash
cd agentic_sdlc/backend
source .venv/bin/activate
python -c "from src.agents.worker.base import AgentWorker; print('worker OK')"
```

Expected: `worker OK`

- [ ] **Step 3: Commit**

```bash
git add agentic_sdlc/backend/src/agents/worker/base.py
git commit -m "feat: add agent worker kafka consumer"
```

---

## Task 5: Conversation Loop (TDD)

**Files:**
- Create: `agentic_sdlc/backend/src/agents/conversation/loop.py`
- Create: `agentic_sdlc/backend/tests/test_conversation_loop.py`

- [ ] **Step 1: Write failing tests**

`agentic_sdlc/backend/tests/test_conversation_loop.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from src.agents.conversation.loop import ConversationLoop, TerminationResult

def _make_config(condition="single_turn", max_turns=5,
                 participants=None, initiator="coder"):
    return {
        "participants": participants or ["coder"],
        "initiator": initiator,
        "termination": {"condition": condition, "max_turns": max_turns},
    }

def test_single_turn_terminates_immediately():
    loop = ConversationLoop(config=_make_config("single_turn"))
    result = loop.check_termination(
        turn_number=1, from_agent="coder", output="some code", config=_make_config("single_turn")
    )
    assert result == TerminationResult.COMPLETE

def test_max_turns_triggers_escalation():
    config = _make_config("reviewer_approves", max_turns=3)
    loop = ConversationLoop(config=config)
    result = loop.check_termination(
        turn_number=3, from_agent="coder", output="still working", config=config
    )
    assert result == TerminationResult.ESCALATE

def test_reviewer_approves_when_signal_present():
    config = _make_config("reviewer_approves", participants=["coder", "reviewer"],
                          initiator="coder")
    loop = ConversationLoop(config=config)
    result = loop.check_termination(
        turn_number=2, from_agent="reviewer",
        output="APPROVED: the code looks good",
        config=config,
    )
    assert result == TerminationResult.COMPLETE

def test_reviewer_not_yet_approved():
    config = _make_config("reviewer_approves", participants=["coder", "reviewer"],
                          initiator="coder")
    loop = ConversationLoop(config=config)
    result = loop.check_termination(
        turn_number=2, from_agent="reviewer",
        output="Please fix the null check on line 5",
        config=config,
    )
    assert result == TerminationResult.CONTINUE

def test_next_participant_alternates():
    config = _make_config(participants=["coder", "reviewer"], initiator="coder")
    loop = ConversationLoop(config=config)
    assert loop.next_participant(current="coder", config=config) == "reviewer"
    assert loop.next_participant(current="reviewer", config=config) == "coder"

def test_next_participant_single_loops_back():
    config = _make_config(participants=["coder"], initiator="coder")
    loop = ConversationLoop(config=config)
    assert loop.next_participant(current="coder", config=config) == "coder"
```

- [ ] **Step 2: Run — verify fails**

```bash
pytest tests/test_conversation_loop.py -v 2>&1 | tail -5
```

Expected: FAIL — module not found.

- [ ] **Step 3: Write loop.py**

`agentic_sdlc/backend/src/agents/conversation/loop.py`:
```python
from enum import Enum

class TerminationResult(str, Enum):
    COMPLETE = "complete"
    CONTINUE = "continue"
    ESCALATE = "escalate"

APPROVAL_SIGNALS = ("APPROVED", "LGTM", "looks good", "approved")

class ConversationLoop:
    def __init__(self, config: dict):
        self.config = config

    def check_termination(self, turn_number: int, from_agent: str,
                          output: str, config: dict) -> TerminationResult:
        termination = config.get("termination", {})
        condition = termination.get("condition", "single_turn")
        max_turns = termination.get("max_turns", 1)

        if turn_number >= max_turns and condition != "single_turn":
            return TerminationResult.ESCALATE

        if condition == "single_turn":
            return TerminationResult.COMPLETE

        if condition == "reviewer_approves":
            participants = config.get("participants", [])
            if len(participants) > 1:
                reviewer = participants[-1]
                if from_agent == reviewer:
                    if any(sig.lower() in output.lower() for sig in APPROVAL_SIGNALS):
                        return TerminationResult.COMPLETE
            return TerminationResult.CONTINUE

        if condition == "tool_success":
            if '"success": true' in output or "'success': True" in output:
                return TerminationResult.COMPLETE
            return TerminationResult.CONTINUE

        return TerminationResult.CONTINUE

    def next_participant(self, current: str, config: dict) -> str:
        participants = config.get("participants", [])
        if len(participants) <= 1:
            return participants[0] if participants else current
        idx = participants.index(current) if current in participants else 0
        return participants[(idx + 1) % len(participants)]
```

- [ ] **Step 4: Run tests — verify pass**

```bash
pytest tests/test_conversation_loop.py -v 2>&1 | tail -8
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add agentic_sdlc/backend/src/agents/conversation/ agentic_sdlc/backend/tests/test_conversation_loop.py
git commit -m "feat: add conversation loop with termination conditions"
```

---

## Task 6: Full Test Suite

- [ ] **Step 1: Run all tests**

```bash
cd agentic_sdlc/backend
source .venv/bin/activate
pytest tests/ -v 2>&1 | tail -15
```

Expected: all tests pass (`22 + 5 + 4 + 6 = 37 passed`)

- [ ] **Step 2: Verify main DB tables still intact**

```bash
python -c "
from src.database import engine
from sqlalchemy import inspect
print('Main DB tables:', sorted(inspect(engine).get_table_names()))
"
```

Expected: 12 tables listed (no drop_all side effects on main DB)

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: plan 3 complete — agent registry, providers, worker, conversation loop"
```

---

## Summary

After Plan 3 you have:
- `POST /agents/registry` — register an agent type
- `GET /agents/registry` — list all agent types
- `GET /agents/registry/{type}` — get by type
- `PATCH /agents/registry/{type}` — update provider config
- `ClaudeCliProvider` — calls `claude -p` subprocess, configurable model
- `ClaudeApiProvider` — calls Anthropic SDK, configurable model + API key
- `AgentWorker` — Kafka consumer on `agent.tasks`, dispatches to correct provider
- `ConversationLoop` — manages multi-turn back-and-forth, evaluates termination
- Test DB isolation — tests no longer affect main DB schema

**Next:** Plan 4 — Human Gate Service (GitHub PR gate, Slack approval, email link).
