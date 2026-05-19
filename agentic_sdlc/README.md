# Agentic Workflow Platform

A general-purpose, event-driven workflow automation platform. Define multi-stage workflows from an admin dashboard, execute them via Kafka-driven agent and human task queues, and configure LLM providers per agent — all without touching code.

## Architecture

```
                        ┌─────────────────┐
                        │   React Dashboard│
                        │  (Admin + Queues)│
                        └────────┬────────┘
                                 │ REST (FastAPI)
                        ┌────────▼────────┐
                        │   FastAPI Backend│
                        │   (Port 8000)    │
                        └────────┬────────┘
                                 │
                    ┌────────────▼────────────┐
                    │          Kafka           │
                    │                          │
                    │  workflow.trigger        │
                    │  agent.tasks             │
                    │  agent.results           │
                    │  agent.conversation      │
                    │  human.tasks             │
                    │  human.results           │
                    │  pipeline.state          │
                    │  pipeline.feedback       │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
    ┌─────────▼──────┐  ┌────────▼───────┐  ┌───────▼──────┐
    │  Agent Workers  │  │  Human Gate    │  │ State Consumer│
    │ (claude_cli /   │  │  Service       │  │  (DB updates) │
    │  claude_api)    │  │ (PR/Slack/Email│  │               │
    └─────────────────┘  └────────────────┘  └───────────────┘
                                 │
                        ┌────────▼────────┐
                        │   PostgreSQL 15  │
                        │   (Port 5433)    │
                        └─────────────────┘
```

## Features

- **Dynamic workflow builder** — define stages, sub-steps, and executor types (agent or human) from the dashboard
- **Agent task queue** — agents consume tasks from Kafka, call the configured LLM, publish results
- **Human task queue** — human approvals via GitHub PR, Slack, or email links
- **Conversation loops** — multi-turn back-and-forth between agents within a sub-step, with configurable termination conditions (`single_turn`, `reviewer_approves`, `max_turns`, `tool_success`)
- **Agent registry** — register agent types and configure provider (Claude CLI or Claude API) per agent from the dashboard
- **Event-driven state** — pipeline state tracked in Postgres via Kafka consumers

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.11, SQLAlchemy 2, Alembic |
| Message broker | Kafka (self-hosted via Docker) |
| Database | PostgreSQL 15 |
| Auth | JWT (Bearer token) + bcrypt |
| LLM providers | Claude CLI (`claude -p`) / Anthropic SDK |
| Frontend | React + JSX, TailwindCSS, Zustand |

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Python 3.11
- `uv` or `pip`

### 1. Start infrastructure

```bash
cd agentic_sdlc
docker compose up -d
```

This starts PostgreSQL (port 5433) and Kafka (port 9092).

### 2. Set up the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env if needed — defaults work with docker-compose
```

Default `.env`:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/agentic_workflow
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
JWT_SECRET=change-me-in-production
JWT_EXPIRE_MINUTES=1440
```

### 4. Run migrations

```bash
cd backend
alembic upgrade head
```

### 5. Start the API

```bash
uvicorn src.main:app --reload
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## API Overview

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Login, returns JWT |

### Workflows
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workflows` | Create a workflow |
| GET | `/workflows` | List workflows |
| POST | `/workflows/{id}/publish` | Publish (activate) a workflow |
| POST | `/workflows/{id}/stages` | Add a stage |
| GET | `/workflows/{id}/stages` | List stages |
| POST | `/stages/{id}/substeps` | Add a sub-step |
| GET | `/stages/{id}/substeps` | List sub-steps |

### Engine
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/runs/trigger` | Trigger a workflow run |
| GET | `/runs/{run_id}` | Get run status |

### State
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/runs?workflow_id=` | List runs for a workflow |
| GET | `/runs/{run_id}/stages` | List stage executions for a run |

### Agent Registry
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/registry` | Register an agent type |
| GET | `/agents/registry` | List all agent types |
| GET | `/agents/registry/{type}` | Get agent by type |
| PATCH | `/agents/registry/{type}` | Update provider config |

## LLM Providers

### Claude CLI
Calls `claude -p` as a subprocess. Useful for local development.

```json
{
  "provider": "claude_cli",
  "provider_config": {
    "cli_path": "claude",
    "model": "claude-sonnet-4-6"
  }
}
```

### Claude API
Calls the Anthropic SDK directly. Requires an API key.

```json
{
  "provider": "claude_api",
  "provider_config": {
    "api_key": "sk-ant-...",
    "model": "claude-sonnet-4-6"
  }
}
```

## Running Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

Tests run against a dedicated `agentic_workflow_test` database — the main DB is never touched by the test suite.

## Project Structure

```
agentic_sdlc/
├── docker-compose.yml          # Postgres + Kafka
└── backend/
    ├── src/
    │   ├── main.py             # FastAPI app + router registration
    │   ├── config.py           # Settings (pydantic-settings)
    │   ├── database.py         # SQLAlchemy engine + session
    │   ├── models/             # ORM models
    │   ├── auth/               # JWT auth + bcrypt
    │   ├── workflows/          # Workflow CRUD
    │   ├── engine/             # Run trigger + dispatch
    │   ├── state/              # Pipeline state consumer
    │   ├── kafka/              # Producer, consumer base, topics
    │   └── agents/
    │       ├── registry/       # Agent type CRUD
    │       ├── worker/         # Kafka consumer + LLM providers
    │       └── conversation/   # Multi-turn loop + termination logic
    ├── tests/
    ├── alembic/                # DB migrations
    └── pyproject.toml
```
