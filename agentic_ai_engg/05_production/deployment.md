# Deployment — Interview Guide

## Serving Patterns for Agents

### REST API (Synchronous)
Best for: short tasks (< 30s), simple request-response.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class AgentRequest(BaseModel):
    query: str
    user_id: str
    session_id: str

class AgentResponse(BaseModel):
    answer: str
    steps_taken: int
    cost_usd: float

@app.post("/agent/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    try:
        result = await agent.run(request.query, request.session_id)
        return AgentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Streaming API (Server-Sent Events)
Best for: real-time UX, long responses.

```python
from fastapi.responses import StreamingResponse
import asyncio

@app.post("/agent/stream")
async def stream_agent(request: AgentRequest):
    async def generate():
        async for chunk in agent.stream(request.query):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Async Job Queue
Best for: long-running tasks, background processing.

```python
from celery import Celery
import redis

celery_app = Celery("agents", broker="redis://localhost:6379")

@celery_app.task
def run_agent_task(query: str, user_id: str, job_id: str):
    result = agent.run(query)
    # Store result in Redis/DB
    redis_client.set(f"job:{job_id}", json.dumps(result), ex=3600)
    return result

# API endpoint: submit job
@app.post("/agent/submit")
async def submit(request: AgentRequest):
    job = run_agent_task.delay(request.query, request.user_id, job_id)
    return {"job_id": job.id, "status_url": f"/agent/status/{job.id}"}

# API endpoint: poll result
@app.get("/agent/status/{job_id}")
async def status(job_id: str):
    result = redis_client.get(f"job:{job_id}")
    if result:
        return {"status": "completed", "result": json.loads(result)}
    return {"status": "pending"}
```

## Containerization

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env.example .env

ENV ANTHROPIC_API_KEY=""
ENV REDIS_URL="redis://redis:6379"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  agent-api:
    build: .
    ports: ["8000:8000"]
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on: [redis, postgres]
  
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: agents
      POSTGRES_PASSWORD: ${DB_PASSWORD}
```

## Scaling Horizontally

```
Load Balancer (nginx/ALB)
    ├── Agent API Pod 1
    ├── Agent API Pod 2
    └── Agent API Pod 3
            ↓ (stateless — all state in external stores)
    ┌────────────────────────────┐
    │  Redis (session/cache)     │
    │  Postgres (state/history)  │
    │  ChromaDB (vector store)   │
    └────────────────────────────┘
```

**Key**: agent API servers must be stateless — all state lives in external stores. Then horizontal scaling is just adding more pods.

## LangServe (LangChain Serving)

```python
from fastapi import FastAPI
from langserve import add_routes

app = FastAPI()

add_routes(
    app,
    agent_runnable,      # any LangChain/LangGraph runnable
    path="/agent",
    enable_feedback_endpoint=True,  # thumbs up/down
    enable_public_trace_link_endpoint=True,  # LangSmith traces
)

# Auto-generates:
# POST /agent/invoke
# POST /agent/stream
# POST /agent/batch
# GET  /agent/playground  (UI for testing)
```

## Common Interview Questions

**Q: How do you handle long-running agent tasks (5+ minutes) in a web API?**
A: Async job pattern: (1) POST /submit → returns job_id immediately, (2) background Celery worker runs agent, (3) client polls GET /status/{job_id} or receives webhook callback on completion. Never block an HTTP connection for > 30s.

**Q: How do you deploy agents without downtime?**
A: (1) Blue-green deployment: bring up new version, switch load balancer, keep old version warm for rollback, (2) Rolling updates in Kubernetes: replace pods one at a time, (3) Feature flags: deploy new agent code, enable for 1% traffic first, scale up after validating.

**Q: What monitoring do you set up on day 1 of production?**
A: (1) Request rate, error rate, latency (RED metrics), (2) Token usage and cost per day, (3) Agent success rate (task completion), (4) LLM API availability, (5) Queue depth (for async jobs). Alert on error rate > 5% and latency p95 > 10s.
