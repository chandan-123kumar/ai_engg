# Agentic Workflow Platform — Plan 2: Workflow Engine + Kafka Routing

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Workflow CRUD API, Kafka producer/consumer infrastructure, Workflow Engine that reads definitions and dispatches tasks to Kafka topics, and the Pipeline State Service that tracks every run in Postgres.

**Architecture:** Workflows and their stages/sub-steps are stored in Postgres and managed via REST. When a run is triggered, the Workflow Engine reads the definition, creates a `WorkflowRun` row, resolves the first stage, and publishes to either `agent.tasks` or `human.tasks` Kafka topic. The Pipeline State Service runs as a background consumer, subscribing to `pipeline.state` events and writing stage transitions to Postgres.

**Tech Stack:** FastAPI, SQLAlchemy, kafka-python, Pydantic v2, pytest, httpx

---

## File Map

```
agentic_sdlc/backend/src/
  kafka/
    __init__.py
    topics.py          ← Kafka topic name constants
    producer.py        ← KafkaProducer singleton wrapper
    consumer.py        ← BaseConsumer class (reusable for all consumers)
  workflows/
    __init__.py
    schemas.py         ← Pydantic request/response schemas
    service.py         ← DB operations: create/get/list/delete workflow, stage, sub-step
    router.py          ← CRUD routes: /workflows, /workflows/{id}/stages, /stages/{id}/substeps
  engine/
    __init__.py
    engine.py          ← WorkflowEngine: trigger_run(), advance_run(), resolve_next_stage()
    router.py          ← POST /runs/trigger, GET /runs/{run_id}
  state/
    __init__.py
    service.py         ← PipelineStateService: consumes pipeline.state, writes to DB
    router.py          ← GET /runs, GET /runs/{run_id}/stages
tests/
  test_workflows.py    ← CRUD API tests
  test_engine.py       ← engine unit tests (mocked Kafka)
  test_state.py        ← state service unit tests
```

---

## Task 1: Kafka Topics + Producer

**Files:**
- Create: `agentic_sdlc/backend/src/kafka/__init__.py`
- Create: `agentic_sdlc/backend/src/kafka/topics.py`
- Create: `agentic_sdlc/backend/src/kafka/producer.py`
- Create: `agentic_sdlc/backend/src/kafka/consumer.py`

- [ ] **Step 1: Create kafka package**

```bash
mkdir -p agentic_sdlc/backend/src/kafka
touch agentic_sdlc/backend/src/kafka/__init__.py
```

- [ ] **Step 2: Write topics.py**

`agentic_sdlc/backend/src/kafka/topics.py`:
```python
WORKFLOW_TRIGGER = "workflow.trigger"
AGENT_TASKS = "agent.tasks"
AGENT_RESULTS = "agent.results"
AGENT_CONVERSATION = "agent.conversation"
HUMAN_TASKS = "human.tasks"
HUMAN_RESULTS = "human.results"
PIPELINE_STATE = "pipeline.state"
PIPELINE_FEEDBACK = "pipeline.feedback"
```

- [ ] **Step 3: Write producer.py**

`agentic_sdlc/backend/src/kafka/producer.py`:
```python
import json
from kafka import KafkaProducer as _KafkaProducer
from src.config import settings

_producer = None

def get_producer() -> _KafkaProducer:
    global _producer
    if _producer is None:
        _producer = _KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
    return _producer

def publish(topic: str, message: dict, key: str = None):
    get_producer().send(topic, value=message, key=key)
    get_producer().flush()
```

- [ ] **Step 4: Write consumer.py**

`agentic_sdlc/backend/src/kafka/consumer.py`:
```python
import json
import threading
from kafka import KafkaConsumer
from src.config import settings

class BaseConsumer(threading.Thread):
    topic: str

    def __init__(self):
        super().__init__(daemon=True)
        self._consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=f"{self.topic}.consumer",
        )

    def handle(self, message: dict):
        raise NotImplementedError

    def run(self):
        for msg in self._consumer:
            self.handle(msg.value)
```

- [ ] **Step 5: Verify imports**

```bash
cd agentic_sdlc/backend
source .venv/bin/activate
python -c "from src.kafka.topics import AGENT_TASKS; from src.kafka.producer import publish; print('kafka OK')"
```

Expected: `kafka OK`

- [ ] **Step 6: Commit**

```bash
git add agentic_sdlc/backend/src/kafka/
git commit -m "feat: add kafka producer, consumer base, and topic constants"
```

---

## Task 2: Workflow CRUD API (TDD)

**Files:**
- Create: `agentic_sdlc/backend/src/workflows/__init__.py`
- Create: `agentic_sdlc/backend/src/workflows/schemas.py`
- Create: `agentic_sdlc/backend/src/workflows/service.py`
- Create: `agentic_sdlc/backend/src/workflows/router.py`
- Create: `agentic_sdlc/backend/tests/test_workflows.py`
- Modify: `agentic_sdlc/backend/src/main.py`

- [ ] **Step 1: Write failing tests**

`agentic_sdlc/backend/tests/test_workflows.py`:
```python
import pytest

@pytest.mark.asyncio
async def test_create_workflow(client, setup_db):
    response = await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]

    response = await client.post("/workflows", json={
        "name": "Full SDLC",
        "trigger": {"source": "linear", "event": "status.tb_ready"}
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Full SDLC"
    assert data["status"] == "draft"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_workflows(client, setup_db):
    reg = await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/workflows", json={"name": "WF1", "trigger": {}}, headers=headers)
    await client.post("/workflows", json={"name": "WF2", "trigger": {}}, headers=headers)

    response = await client.get("/workflows", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

@pytest.mark.asyncio
async def test_add_stage_to_workflow(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()

    response = await client.post(f"/workflows/{wf['id']}/stages", json={
        "name": "Planning",
        "order": 1,
        "executor_type": "agent",
        "config": {}
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Planning"

@pytest.mark.asyncio
async def test_add_substep_to_stage(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    stage = (await client.post(f"/workflows/{wf['id']}/stages", json={
        "name": "Code Gen", "order": 1, "executor_type": "agent", "config": {}
    }, headers=headers)).json()

    response = await client.post(f"/stages/{stage['id']}/substeps", json={
        "name": "Generate code",
        "order": 1,
        "executor_type": "agent",
        "agent_conversation_config": {
            "participants": ["coder", "reviewer"],
            "initiator": "coder",
            "termination": {"condition": "reviewer_approves", "max_turns": 5}
        }
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Generate code"

@pytest.mark.asyncio
async def test_publish_workflow(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    response = await client.post(f"/workflows/{wf['id']}/publish", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "active"
```

- [ ] **Step 2: Run — verify fails**

```bash
cd agentic_sdlc/backend
source .venv/bin/activate
pytest tests/test_workflows.py -v 2>&1 | tail -5
```

Expected: FAIL — `404 Not Found` (routes not yet registered)

- [ ] **Step 3: Write schemas.py**

`agentic_sdlc/backend/src/workflows/schemas.py`:
```python
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
```

- [ ] **Step 4: Write service.py**

`agentic_sdlc/backend/src/workflows/service.py`:
```python
import uuid
from sqlalchemy.orm import Session
from src.models.workflow import Workflow, Stage, SubStep, WorkflowStatus

def create_workflow(db: Session, user_id: str, name: str, trigger: dict) -> Workflow:
    wf = Workflow(id=uuid.uuid4(), user_id=user_id, name=name, config={"trigger": trigger})
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return wf

def list_workflows(db: Session, user_id: str) -> list[Workflow]:
    return db.query(Workflow).filter(Workflow.user_id == user_id).all()

def get_workflow(db: Session, workflow_id: str, user_id: str) -> Workflow | None:
    return db.query(Workflow).filter(
        Workflow.id == workflow_id, Workflow.user_id == user_id
    ).first()

def publish_workflow(db: Session, workflow_id: str, user_id: str) -> Workflow | None:
    wf = get_workflow(db, workflow_id, user_id)
    if not wf:
        return None
    wf.status = WorkflowStatus.active
    db.commit()
    db.refresh(wf)
    return wf

def add_stage(db: Session, workflow_id: str, name: str, order: int,
              executor_type: str, gate_type: str | None, config: dict) -> Stage:
    stage = Stage(
        id=uuid.uuid4(), workflow_id=workflow_id,
        name=name, order=order, executor_type=executor_type,
        gate_type=gate_type, config=config,
    )
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage

def get_stages(db: Session, workflow_id: str) -> list[Stage]:
    return db.query(Stage).filter(Stage.workflow_id == workflow_id).order_by(Stage.order).all()

def add_sub_step(db: Session, stage_id: str, name: str, order: int, executor_type: str,
                 agent_conversation_config: dict | None, on_complete: str | None,
                 on_reject: str | None) -> SubStep:
    ss = SubStep(
        id=uuid.uuid4(), stage_id=stage_id, name=name, order=order,
        executor_type=executor_type,
        agent_conversation_config=agent_conversation_config,
        on_complete=on_complete, on_reject=on_reject,
    )
    db.add(ss)
    db.commit()
    db.refresh(ss)
    return ss

def get_sub_steps(db: Session, stage_id: str) -> list[SubStep]:
    return db.query(SubStep).filter(SubStep.stage_id == stage_id).order_by(SubStep.order).all()
```

- [ ] **Step 5: Write router.py**

`agentic_sdlc/backend/src/workflows/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.workflows import service
from src.workflows.schemas import (
    WorkflowCreate, WorkflowResponse,
    StageCreate, StageResponse,
    SubStepCreate, SubStepResponse,
)

router = APIRouter()

@router.post("/workflows", status_code=201, response_model=WorkflowResponse)
def create_workflow(body: WorkflowCreate, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    wf = service.create_workflow(db, str(user.id), body.name, body.trigger)
    return {**wf.__dict__, "trigger": wf.config.get("trigger", {})}

@router.get("/workflows", response_model=list[WorkflowResponse])
def list_workflows(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wfs = service.list_workflows(db, str(user.id))
    return [{**w.__dict__, "trigger": w.config.get("trigger", {})} for w in wfs]

@router.post("/workflows/{workflow_id}/publish", response_model=WorkflowResponse)
def publish_workflow(workflow_id: str, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    wf = service.publish_workflow(db, workflow_id, str(user.id))
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {**wf.__dict__, "trigger": wf.config.get("trigger", {})}

@router.post("/workflows/{workflow_id}/stages", status_code=201, response_model=StageResponse)
def add_stage(workflow_id: str, body: StageCreate, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    wf = service.get_workflow(db, workflow_id, str(user.id))
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return service.add_stage(db, workflow_id, body.name, body.order,
                              body.executor_type, body.gate_type, body.config)

@router.get("/workflows/{workflow_id}/stages", response_model=list[StageResponse])
def list_stages(workflow_id: str, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return service.get_stages(db, workflow_id)

@router.post("/stages/{stage_id}/substeps", status_code=201, response_model=SubStepResponse)
def add_sub_step(stage_id: str, body: SubStepCreate, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    return service.add_sub_step(
        db, stage_id, body.name, body.order, body.executor_type,
        body.agent_conversation_config, body.on_complete, body.on_reject,
    )

@router.get("/stages/{stage_id}/substeps", response_model=list[SubStepResponse])
def list_sub_steps(stage_id: str, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return service.get_sub_steps(db, stage_id)
```

- [ ] **Step 6: Register router in main.py**

`agentic_sdlc/backend/src/main.py`:
```python
from fastapi import FastAPI
from src.health.router import router as health_router
from src.auth.router import router as auth_router
from src.workflows.router import router as workflow_router

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workflow_router)
```

- [ ] **Step 7: Run tests — verify pass**

```bash
pytest tests/test_workflows.py -v
```

Expected: 5 tests `PASSED`

- [ ] **Step 8: Commit**

```bash
git add agentic_sdlc/backend/src/workflows/ agentic_sdlc/backend/src/main.py agentic_sdlc/backend/tests/test_workflows.py
git commit -m "feat: add workflow CRUD API with stages and sub-steps"
```

---

## Task 3: Workflow Engine (TDD)

**Files:**
- Create: `agentic_sdlc/backend/src/engine/__init__.py`
- Create: `agentic_sdlc/backend/src/engine/engine.py`
- Create: `agentic_sdlc/backend/src/engine/router.py`
- Create: `agentic_sdlc/backend/tests/test_engine.py`
- Modify: `agentic_sdlc/backend/src/main.py`

- [ ] **Step 1: Write failing tests**

`agentic_sdlc/backend/tests/test_engine.py`:
```python
import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_trigger_run_creates_run(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish") as mock_pub:
        response = await client.post("/runs/trigger", json={
            "workflow_id": wf["id"],
            "trigger_payload": {"source": "linear", "ticket_id": "ABC-1"}
        }, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["workflow_id"] == wf["id"]
    assert data["status"] == "running"
    assert "id" in data

@pytest.mark.asyncio
async def test_trigger_run_draft_workflow_fails(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()

    response = await client.post("/runs/trigger", json={
        "workflow_id": wf["id"],
        "trigger_payload": {}
    }, headers=headers)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_get_run(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish"):
        run = (await client.post("/runs/trigger", json={
            "workflow_id": wf["id"], "trigger_payload": {}
        }, headers=headers)).json()

    response = await client.get(f"/runs/{run['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == run["id"]

@pytest.mark.asyncio
async def test_trigger_publishes_to_kafka_when_stage_exists(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/stages", json={
        "name": "Planning", "order": 1, "executor_type": "agent", "config": {}
    }, headers=headers)
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish") as mock_pub:
        await client.post("/runs/trigger", json={
            "workflow_id": wf["id"], "trigger_payload": {"ticket": "ABC-1"}
        }, headers=headers)
        assert mock_pub.called
        call_args = mock_pub.call_args
        assert call_args[0][0] == "agent.tasks"
```

- [ ] **Step 2: Run — verify fails**

```bash
pytest tests/test_engine.py -v 2>&1 | tail -5
```

Expected: FAIL — routes not yet defined.

- [ ] **Step 3: Write engine.py**

`agentic_sdlc/backend/src/engine/engine.py`:
```python
import uuid
from sqlalchemy.orm import Session
from src.models.run import WorkflowRun, StageExecution, RunStatus, ExecutionStatus
from src.models.workflow import Workflow, Stage, WorkflowStatus
from src.models.task import AgentTask, HumanTask, TaskStatus, HumanTaskStatus
from src.kafka.producer import publish
from src.kafka import topics

def trigger_run(db: Session, workflow_id: str, trigger_payload: dict) -> WorkflowRun:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow or workflow.status != WorkflowStatus.active:
        raise ValueError("Workflow not found or not active")

    run = WorkflowRun(
        id=uuid.uuid4(),
        workflow_id=workflow_id,
        trigger_payload=trigger_payload,
        status=RunStatus.running,
    )
    db.add(run)
    db.flush()

    first_stage = (
        db.query(Stage)
        .filter(Stage.workflow_id == workflow_id)
        .order_by(Stage.order)
        .first()
    )

    if first_stage:
        _dispatch_stage(db, run, first_stage, trigger_payload)

    db.commit()
    db.refresh(run)
    return run

def _dispatch_stage(db: Session, run: WorkflowRun, stage: Stage, payload: dict):
    run.current_stage_id = stage.id

    execution = StageExecution(
        id=uuid.uuid4(),
        run_id=run.id,
        stage_id=stage.id,
        executor_type=stage.executor_type,
        status=ExecutionStatus.running,
    )
    db.add(execution)
    db.flush()

    event = {
        "run_id": str(run.id),
        "workflow_id": str(run.workflow_id),
        "stage_id": str(stage.id),
        "stage_execution_id": str(execution.id),
        "executor_type": stage.executor_type,
        "payload": payload,
    }

    if stage.executor_type == "agent":
        publish(topics.AGENT_TASKS, event, key=str(run.id))
    else:
        publish(topics.HUMAN_TASKS, event, key=str(run.id))

    publish(topics.PIPELINE_STATE, {
        **event,
        "event": "stage_started",
    }, key=str(run.id))

def get_run(db: Session, run_id: str) -> WorkflowRun | None:
    return db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()

def list_runs(db: Session, workflow_id: str) -> list[WorkflowRun]:
    return db.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).all()
```

- [ ] **Step 4: Write engine router.py**

`agentic_sdlc/backend/src/engine/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.engine import engine

router = APIRouter()

class TriggerRequest(BaseModel):
    workflow_id: str
    trigger_payload: dict = {}

class RunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_payload: dict

    model_config = {"from_attributes": True}

@router.post("/runs/trigger", status_code=201, response_model=RunResponse)
def trigger_run(body: TriggerRequest, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    try:
        run = engine.trigger_run(db, body.workflow_id, body.trigger_payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": str(run.id), "workflow_id": str(run.workflow_id),
            "status": run.status, "trigger_payload": run.trigger_payload}

@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    run = engine.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"id": str(run.id), "workflow_id": str(run.workflow_id),
            "status": run.status, "trigger_payload": run.trigger_payload}
```

- [ ] **Step 5: Create __init__.py**

```bash
touch agentic_sdlc/backend/src/engine/__init__.py
```

- [ ] **Step 6: Register engine router in main.py**

`agentic_sdlc/backend/src/main.py`:
```python
from fastapi import FastAPI
from src.health.router import router as health_router
from src.auth.router import router as auth_router
from src.workflows.router import router as workflow_router
from src.engine.router import router as engine_router

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workflow_router)
app.include_router(engine_router)
```

- [ ] **Step 7: Run tests — verify pass**

```bash
pytest tests/test_engine.py -v
```

Expected: 4 tests `PASSED`

- [ ] **Step 8: Commit**

```bash
git add agentic_sdlc/backend/src/engine/ agentic_sdlc/backend/src/main.py agentic_sdlc/backend/tests/test_engine.py
git commit -m "feat: add workflow engine with run trigger and kafka dispatch"
```

---

## Task 4: Pipeline State Service (TDD)

**Files:**
- Create: `agentic_sdlc/backend/src/state/__init__.py`
- Create: `agentic_sdlc/backend/src/state/service.py`
- Create: `agentic_sdlc/backend/src/state/router.py`
- Create: `agentic_sdlc/backend/tests/test_state.py`
- Modify: `agentic_sdlc/backend/src/main.py`

- [ ] **Step 1: Write failing tests**

`agentic_sdlc/backend/tests/test_state.py`:
```python
import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_list_runs_empty(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    response = await client.get(f"/runs?workflow_id={wf['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_list_runs_after_trigger(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish"):
        await client.post("/runs/trigger", json={
            "workflow_id": wf["id"], "trigger_payload": {}
        }, headers=headers)

    response = await client.get(f"/runs?workflow_id={wf['id']}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "running"

@pytest.mark.asyncio
async def test_get_run_stages(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/stages", json={
        "name": "Planning", "order": 1, "executor_type": "agent", "config": {}
    }, headers=headers)
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish"):
        run = (await client.post("/runs/trigger", json={
            "workflow_id": wf["id"], "trigger_payload": {}
        }, headers=headers)).json()

    response = await client.get(f"/runs/{run['id']}/stages", headers=headers)
    assert response.status_code == 200
    stages = response.json()
    assert len(stages) == 1
    assert stages[0]["status"] == "running"
```

- [ ] **Step 2: Run — verify fails**

```bash
pytest tests/test_state.py -v 2>&1 | tail -5
```

Expected: FAIL — routes not yet defined.

- [ ] **Step 3: Write state service.py**

`agentic_sdlc/backend/src/state/service.py`:
```python
from sqlalchemy.orm import Session
from src.models.run import WorkflowRun, StageExecution
from src.kafka.consumer import BaseConsumer
from src.kafka import topics
from src.database import SessionLocal

def list_runs(db: Session, workflow_id: str) -> list[WorkflowRun]:
    return db.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).all()

def list_stage_executions(db: Session, run_id: str) -> list[StageExecution]:
    return db.query(StageExecution).filter(StageExecution.run_id == run_id).all()

class PipelineStateConsumer(BaseConsumer):
    topic = topics.PIPELINE_STATE

    def handle(self, message: dict):
        db = SessionLocal()
        try:
            event = message.get("event")
            run_id = message.get("run_id")
            if not run_id:
                return
            if event == "stage_completed":
                run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
                if run:
                    run.status = message.get("run_status", run.status)
                    db.commit()
        finally:
            db.close()
```

- [ ] **Step 4: Write state router.py**

`agentic_sdlc/backend/src/state/router.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.state import service

router = APIRouter()

class RunSummary(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_payload: dict

class StageExecutionSummary(BaseModel):
    id: str
    stage_id: str
    executor_type: str
    status: str

@router.get("/runs")
def list_runs(workflow_id: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    runs = service.list_runs(db, workflow_id)
    return [
        {"id": str(r.id), "workflow_id": str(r.workflow_id),
         "status": r.status, "trigger_payload": r.trigger_payload}
        for r in runs
    ]

@router.get("/runs/{run_id}/stages")
def list_run_stages(run_id: str, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    execs = service.list_stage_executions(db, run_id)
    return [
        {"id": str(e.id), "stage_id": str(e.stage_id),
         "executor_type": e.executor_type, "status": e.status}
        for e in execs
    ]
```

- [ ] **Step 5: Create __init__.py**

```bash
touch agentic_sdlc/backend/src/state/__init__.py
```

- [ ] **Step 6: Register state router in main.py**

`agentic_sdlc/backend/src/main.py`:
```python
from fastapi import FastAPI
from src.health.router import router as health_router
from src.auth.router import router as auth_router
from src.workflows.router import router as workflow_router
from src.engine.router import router as engine_router
from src.state.router import router as state_router

app = FastAPI(title="Agentic Workflow Platform")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workflow_router)
app.include_router(engine_router)
app.include_router(state_router)
```

- [ ] **Step 7: Run tests — verify pass**

```bash
pytest tests/test_state.py -v
```

Expected: 3 tests `PASSED`

- [ ] **Step 8: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests `PASSED`

- [ ] **Step 9: Commit**

```bash
git add agentic_sdlc/backend/src/state/ agentic_sdlc/backend/src/main.py agentic_sdlc/backend/tests/test_state.py
git commit -m "feat: add pipeline state service and run/stage query endpoints"
```

---

## Task 5: Alembic Migration for Plan 2

No new tables — all models were created in Plan 1. Run autogenerate to confirm no drift:

- [ ] **Step 1: Check for schema drift**

```bash
cd agentic_sdlc/backend
source .venv/bin/activate
alembic check
```

Expected: `No new upgrade operations detected.`

- [ ] **Step 2: Final commit on branch**

```bash
git add .
git commit -m "feat: plan 2 complete — workflow engine, kafka routing, state service"
```

---

## Summary

After Plan 2 you have:
- `POST /workflows` — create workflow
- `GET /workflows` — list user's workflows
- `POST /workflows/{id}/stages` — add stage
- `POST /stages/{id}/substeps` — add sub-step
- `POST /workflows/{id}/publish` — activate workflow
- `POST /runs/trigger` — trigger a run (dispatches to Kafka)
- `GET /runs/{id}` — get run status
- `GET /runs?workflow_id=` — list runs for a workflow
- `GET /runs/{id}/stages` — stage execution history
- Kafka producer publishing to `agent.tasks`, `human.tasks`, `pipeline.state`
- `PipelineStateConsumer` background thread consuming `pipeline.state`

**Next:** Plan 3 — Agent Workers + Conversation Loops (Claude CLI + API integration, back-and-forth sub-step execution).
