# Agentic Workflow Platform — Design Spec
**Date:** 2026-05-19
**Status:** Approved

---

## Overview

A general-purpose agentic workflow automation platform where users define multi-stage workflows with sub-steps. Each sub-step is executed by either an AI agent or a human. Agents can converse back-and-forth within a sub-step until a termination condition is met. The platform ships with a SDLC workflow out of the box but supports any domain (marketing, content, bug triage, etc.).

**Primary trigger event:** Tech Brief (TB) ready — a Linear ticket moves to a specific status, firing a webhook that starts the pipeline.

---

## 1. Architecture Overview

### Components

```
┌──────────────────────────────────────────────────────────────────┐
│                      AGENTIC WORKFLOW SYSTEM                     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    FRONTEND (Dashboard)                  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │    │
│  │  │ Agent Queue │  │ Human Queue │  │  Admin Panel   │  │    │
│  │  │  (tasks)    │  │  (tasks)    │  │ (workflow def) │  │    │
│  │  └─────────────┘  └─────────────┘  └────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────────────────▼─────────────────────────────┐    │
│  │                     BACKEND SERVICES                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐   │    │
│  │  │  Workflow    │  │   Pipeline   │  │   Webhook   │   │    │
│  │  │   Engine     │  │State Service │  │   Receiver  │   │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘   │    │
│  └───────────────────────────┬─────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────────────────▼─────────────────────────────┐    │
│  │                    KAFKA EVENT BUS                       │    │
│  └───────────────────────────┬─────────────────────────────┘    │
│                              │                                   │
│         ┌────────────────────┴──────────────────┐               │
│         ▼                                       ▼               │
│  ┌─────────────┐                        ┌──────────────┐        │
│  │Agent Workers│                        │  Human Gate  │        │
│  │(pluggable)  │                        │   Service    │        │
│  └─────────────┘                        └──────────────┘        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  STORAGE: Postgres (workflow defs, run state, tasks)     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Design Approach
- **Kafka per-topic per event type** (generic topics, not per-stage) — all workflows share the same topics; messages carry `workflow_id`, `run_id`, `stage_id`, `sub_step_id`, `user_id` for routing
- **Pipeline State Service** — lightweight Postgres-backed observer that tracks run state via all Kafka events; exposes REST API for dashboard; does not dispatch or control agents
- **Workflow Engine** — reads workflow definitions, routes events to agent or human queues, advances runs based on completion events

---

## 2. Multi-Workflow, Multi-User Model

One user can have many workflows across different domains. Each workflow is versioned — active runs complete on the version they started on.

### Example Workflows (same engine)

| Workflow | Trigger | Domain |
|---|---|---|
| Full SDLC | Linear TB Ready | Engineering |
| Marketing Campaign | Notion doc ready | Marketing |
| Content Pipeline | Cron / RSS feed | Content |
| Bug Triage | GitHub issue opened | Engineering |

### Postgres Schema

```sql
users               — id, name, email
workflows           — id, user_id, name, version, config JSONB, status (draft/active)
stages              — id, workflow_id, name, order, executor_type, gate_type, config JSONB
sub_steps           — id, stage_id, name, order, executor_type, agent_conversation_config JSONB, on_complete, on_reject
workflow_runs       — id, workflow_id, trigger_payload, current_stage_id, status
stage_executions    — id, run_id, stage_id, executor_type, status, result, created_at
sub_step_executions — id, stage_execution_id, sub_step_id, status, result
agent_tasks         — id, sub_step_execution_id, agent_type, payload, status
human_tasks         — id, sub_step_execution_id, gate_type, payload, status
agent_conversations — id, sub_step_execution_id, turn_number, from_agent, to_agent, message JSONB, status
agent_registry      — agent_type, name, description, input_schema JSONB, output_schema JSONB, endpoint, provider (claude_cli|claude_api), provider_config JSONB
```

---

## 3. Workflow Engine & Kafka Routing

### Kafka Topics

| Topic | Purpose |
|---|---|
| `workflow.trigger` | Inbound trigger events (Linear, Jira, cron, manual) |
| `agent.tasks` | All agent tasks across all workflows |
| `agent.results` | Agent completion / failure events |
| `agent.conversation` | Back-and-forth messages between agents within a sub-step |
| `human.tasks` | All human gate tasks |
| `human.results` | Human approve / reject events |
| `pipeline.state` | All stage and sub-step transitions (consumed by State Service) |
| `pipeline.feedback` | Monitor agent output fed back to trigger source |

### Workflow Engine Flow

```
Trigger Event Received
        │
        ▼
Create Run → Resolve Stage 1 → Resolve Sub-step 1
        │
        ▼
Stage Router:
  executor_type == "agent"  → publish to agent.tasks
  executor_type == "human"  → publish to human.tasks → fire gate (PR / Slack / email)
        │
        ▼
Wait for result event
  success → resolve next sub-step or advance stage
  failure → on_reject path (retry / reroute / halt)
  timeout → escalate to human queue
```

### Workflow Definition (JSONB config)

```json
{
  "workflow_id": "sdlc-v1",
  "name": "Full SDLC",
  "trigger": { "source": "linear", "event": "status.tb_ready" },
  "stages": [
    {
      "id": "planning",
      "name": "Planning",
      "executor": "agent",
      "sub_steps": [
        {
          "id": "breakdown",
          "name": "Break down tech brief",
          "executor": "agent",
          "agent_conversation_config": {
            "participants": ["planner"],
            "initiator": "planner",
            "termination": { "condition": "single_turn" }
          }
        }
      ],
      "on_complete": "code_gen"
    },
    {
      "id": "code_gen",
      "name": "Code Generation",
      "executor": "agent",
      "sub_steps": [
        {
          "id": "generate_code",
          "name": "Generate and review code",
          "executor": "agent",
          "agent_conversation_config": {
            "participants": ["coder", "reviewer"],
            "initiator": "coder",
            "termination": { "condition": "reviewer_approves", "max_turns": 5 }
          }
        },
        {
          "id": "open_pr",
          "name": "Open PR",
          "executor": "agent",
          "agent_conversation_config": {
            "participants": ["github_agent"],
            "initiator": "github_agent",
            "termination": { "condition": "single_turn" }
          }
        }
      ],
      "on_complete": "code_review"
    },
    {
      "id": "code_review",
      "name": "Code Review",
      "executor": "human",
      "gate": "github_pr",
      "on_approve": "testing",
      "on_reject": "code_gen"
    }
  ]
}
```

---

## 4. Sub-Steps & Agent Back-and-Forth

### Stage → Sub-Steps → Agent Turns

Each stage contains ordered sub-steps. Each sub-step runs an agent conversation loop until a termination condition is met.

```
Stage: Code Generation
  │
  ├── Sub-step 1: Break down brief       → Planner (single turn)
  ├── Sub-step 2: Generate & review code → Coder ↔ Reviewer (up to 5 turns)
  │     turn 1: Coder produces code
  │     turn 2: Reviewer gives feedback
  │     turn 3: Coder refines
  │     ... until Reviewer approves OR max_turns reached
  ├── Sub-step 3: Generate unit tests    → QA ↔ Coder (until tests pass)
  └── Sub-step 4: Open PR               → GitHub Agent (single turn) → human gate
```

### Termination Conditions

| Condition | Behaviour |
|---|---|
| `single_turn` | Completes after one agent response |
| `reviewer_approves` | Named agent must emit an approval signal |
| `max_turns` | Hard limit; escalates to human queue if reached without approval |
| `tool_success` | Completes when a tool call returns success (e.g. tests pass) |

### Agent Conversation Loop

```
Sub-Step Executor
  │
  ├── Turn 1: dispatch initiator agent via agent.tasks
  └── LOOP:
        agent produces output → publish to agent.conversation
        route to next participant
        check termination condition:
          met     → mark sub-step complete → next sub-step
          max_turns → escalate to human.tasks
          failure → on_reject path
```

### Human Gate Types

| Gate | Trigger | Completion Signal |
|---|---|---|
| `github_pr` | Open PR via GitHub API | PR merged / closed |
| `slack_approval` | Post message with Approve/Reject buttons | Button click callback |
| `email_link` | Send email with token URL | Token URL hit |
| `linear_status` | Update Linear ticket status | Ticket moves to next status |

---

## 5. Frontend

### Tech Stack
- **Frontend:** React + JSX, TailwindCSS
- **Real-time:** WebSocket (pipeline state events pushed live)
- **State:** Zustand
- **Backend API:** FastAPI (Python)

### Dashboard Views

**My Workflows (Home)**
- List of user's workflows with status (draft/active), active run count, and actions
- New Workflow button opens Admin Panel builder

**Workflow Run View**
- Stage pipeline progress bar (visual stage chain with status indicators)
- Active sub-step with current turn number and conversation thread link
- Agent Queue: tasks currently running or queued for agents
- Human Queue: tasks waiting for human action with context and action buttons

**Agent Conversation Thread (drill-down)**
- Turn-by-turn messages between agents
- Each turn shows: from_agent, to_agent, message summary, timestamp
- Status badge: in progress / approved / escalated

### Admin Panel — Workflow Builder

- **Form-based stage list:** add, reorder, delete stages; set executor type and gate type per stage
- **Sub-step editor per stage:** add, reorder sub-steps; configure agent participants, initiator, termination condition
- **JSON preview pane:** live preview of workflow config JSONB; user can directly edit JSON to override
- **Publish flow:** Save Draft → Publish (creates new version; existing runs unaffected)
- **Trigger config:** select source (Linear, Jira, cron, manual), set event condition

### Agent Registry (Admin)
- List registered agent types with name, description, input/output schema
- Register new agent type with endpoint URL
- Configure LLM provider per agent: `claude_cli` (default) or `claude_api`
  - Claude CLI: set CLI path and model flag
  - Claude API: set API key and model ID
- Available agent types appear in sub-step editor dropdowns

---

## 6. Feedback Loop

```
Monitor Agent (post-deploy / post-publish)
  │
  ├── domain-specific: watches error rates, metrics, engagement
  ├── publishes anomalies to: pipeline.feedback
  │
  └── Feedback Handler:
        → updates originating Linear/Jira ticket with findings
        → optionally triggers a new workflow run (e.g. hotfix workflow)
```

---

## 7. Out of Scope (v1)

- Multi-tenancy / organisation-level access control (single user per account)
- Agent fine-tuning or custom model hosting
- Visual drag-and-drop workflow builder (form-based + JSON in v1)
- Billing / usage metering

---

## 8. Decisions

- **LLM Provider:** Claude Code CLI by default. Also supports direct Anthropic API. Provider is configurable per-agent from the dashboard — each agent in the registry has a `provider` field (`claude_cli` | `claude_api`) and associated config (API key, model, CLI path). New providers can be added via the agent registry.
- **Kafka:** Self-hosted (Docker Compose for local dev, bare-metal/VM for production).
- **Authentication:** Basic username + password. Credentials stored as bcrypt hashes in Postgres. Session via signed JWT stored in httpOnly cookie.
