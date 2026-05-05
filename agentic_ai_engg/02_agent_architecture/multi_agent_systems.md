# Multi-Agent Systems — Interview Guide

## Why Multi-Agent?

Single agents have limits:
- Context window overflow on large tasks
- Hard to parallelize with one agent
- Specialization improves quality
- Easier to test/debug individual components

Multi-agent enables: parallelism, specialization, peer review, and scale beyond context limits.

## Orchestration Patterns

### 1. Supervisor / Orchestrator
One controller agent delegates to worker agents.

```
User Query
    ↓
Orchestrator (plans and routes)
    ├── Agent A (researcher)
    ├── Agent B (coder)
    └── Agent C (writer)
    ↓
Synthesized Answer
```

```python
class OrchestratorAgent:
    def run(self, task: str):
        plan = self.plan(task)  # LLM creates sub-task list
        
        results = {}
        for step in plan.steps:
            agent = self.select_agent(step)  # route to specialist
            results[step.id] = agent.run(step.description)
        
        return self.synthesize(task, results)
```

### 2. Peer-to-Peer / Pipeline
Agents pass work in sequence, each transforming the output.

```
Agent A (gather data) → Agent B (analyze) → Agent C (write report)
```

Good for: document processing pipelines, code → review → refactor chains.

### 3. Debate / Critic Pattern
Two agents argue; a judge decides the winner.

```
Agent A generates answer
Agent B critiques Agent A
Agent A defends / revises
Judge evaluates and selects best
```

Improves accuracy on complex reasoning tasks (math, code, factual questions).

### 4. Hierarchical
Multi-level delegation: manager → team lead → worker.

```
CEO Agent
├── Engineering Manager Agent
│   ├── Backend Dev Agent
│   └── Frontend Dev Agent
└── Product Manager Agent
    └── Researcher Agent
```

### 5. Parallel Fan-Out
All sub-tasks run simultaneously; results aggregated.

```python
import asyncio

async def parallel_research(topics: list[str]) -> list[str]:
    tasks = [research_agent.run(topic) for topic in topics]
    results = await asyncio.gather(*tasks)
    return results
```

## Communication Patterns

### Shared Message Queue
```python
from collections import deque

class AgentBus:
    def __init__(self):
        self.queues: dict[str, deque] = {}
    
    def send(self, to: str, message: dict):
        self.queues.setdefault(to, deque()).append(message)
    
    def receive(self, agent_id: str) -> dict | None:
        if queue := self.queues.get(agent_id):
            return queue.popleft() if queue else None
```

### Shared State / Blackboard
All agents read/write to a central state object. Simple but can cause race conditions in async systems.

```python
@dataclass
class SharedWorkspace:
    task: str
    research_results: list = field(default_factory=list)
    analysis: str = ""
    draft: str = ""
    status: str = "pending"
```

### Handoff Protocol
Explicit structured handoff between agents.

```python
@dataclass
class Handoff:
    from_agent: str
    to_agent: str
    task: str
    context: dict        # what to pass along
    artifacts: list      # files, data produced
    instructions: str    # specific guidance for next agent
```

## Agent Roles

| Role | Responsibility | Example |
|---|---|---|
| Orchestrator | Plans, delegates, synthesizes | Project manager |
| Researcher | Gathers information | Retrieval + web search |
| Analyst | Interprets data | Data analysis agent |
| Critic/Reviewer | Finds flaws, validates | Code reviewer |
| Executor | Takes actions | Browser, code runner |
| Summarizer | Condenses information | Report writer |

## LangGraph Multi-Agent

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("orchestrator", orchestrator_agent)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("writer", writer_agent)

# Add edges
workflow.set_entry_point("orchestrator")
workflow.add_conditional_edges(
    "orchestrator",
    route_task,  # function that returns next node name
    {
        "research": "researcher",
        "write": "writer",
        "done": END
    }
)
workflow.add_edge("researcher", "orchestrator")
workflow.add_edge("writer", "orchestrator")

app = workflow.compile()
```

## Trust and Safety in Multi-Agent

### Trust Hierarchy
- **Human**: highest trust (always override)
- **Orchestrator**: trusted, sets task scope
- **Worker agents**: limited trust — validate their outputs before acting
- **External systems**: untrusted — sanitize all inputs

### Common Vulnerabilities
- **Prompt injection via tool results**: web content tells agent to ignore instructions
- **Agent impersonation**: one agent claims to be another
- **Scope creep**: orchestrator grants worker more permissions than needed

### Defense Pattern
```python
def validate_agent_action(action: AgentAction, allowed_scope: set):
    if action.tool not in allowed_scope:
        raise PermissionError(
            f"Agent attempted {action.tool} outside allowed scope: {allowed_scope}"
        )
    return action
```

## Scalability Considerations

| Problem | Solution |
|---|---|
| Too many LLM calls | Parallelize independent agents; cache results |
| Agent coordination overhead | Use async message passing |
| Debugging agent failures | Structured logging with agent IDs + trace IDs |
| Cost blowup | Token budgets per agent, circuit breakers |
| Infinite loops | Global iteration counter across all agents |

## Common Interview Questions

**Q: How do multi-agent systems differ from a single agent with many tools?**
A: Multi-agent: independent LLM instances running in parallel, each with their own context and specialization. Better for tasks that need parallelism or specialization. Single agent + many tools: one LLM sequentially calling tools — simpler but no parallelism and context fills up faster with many tool results.

**Q: Design a multi-agent system for automated code review.**
A: (1) Orchestrator receives PR diff, creates review plan, (2) Security Agent checks for vulnerabilities, (3) Style Agent checks formatting/conventions, (4) Logic Agent evaluates correctness, all run in parallel, (5) Synthesizer aggregates findings, removes duplicates, ranks by severity, (6) Returns structured review report.

**Q: How do you ensure agents don't interfere with each other's work?**
A: (1) Scoped state — each agent has its own working memory, (2) Message passing with explicit handoffs, (3) Locking for shared resources (files, DB writes), (4) Explicit handoff protocols rather than shared mutable state.

**Q: What's the hardest problem in multi-agent systems?**
A: Coordination and error propagation. When agent B fails after agent A has already taken irreversible actions, you need rollback mechanisms or compensating transactions. Also, debugging is hard — need full distributed tracing across agent boundaries.
