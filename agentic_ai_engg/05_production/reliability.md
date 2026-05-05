# Reliability — Interview Guide

## Failure Modes in Production Agents

| Failure | Cause | Impact |
|---|---|---|
| LLM API timeout | High load, network | Agent stuck, user waiting |
| Context overflow | Long conversation | Hard stop, lost progress |
| Tool failure | External service down | Agent loops or errors |
| Hallucination | LLM generates false info | Wrong tool args, bad decisions |
| Infinite loop | Agent can't find answer | Runaway cost, stuck user |
| Rate limit exceeded | Too many API calls | Full outage for all users |
| Prompt injection | Malicious tool result | Security breach |

## Retry with Exponential Backoff

```python
import asyncio
import random
from anthropic import RateLimitError, APIStatusError

async def llm_call_with_retry(messages: list, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            return await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=messages
            )
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)  # jitter
            await asyncio.sleep(wait)
        except APIStatusError as e:
            if e.status_code >= 500:  # server errors: retry
                wait = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait)
            else:  # client errors (400): don't retry
                raise
```

## Circuit Breaker

Prevent cascading failures when a dependency is down:

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"       # normal operation
    OPEN = "open"           # failing, reject calls
    HALF_OPEN = "half_open" # testing if recovered

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at: datetime | None = None
    
    def call(self, fn, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.opened_at > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit open — service unavailable")
        
        try:
            result = fn(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()

# Usage
llm_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
result = llm_breaker.call(client.messages.create, model="...", messages=[...])
```

## Fallback Strategies

```python
async def llm_with_fallback(messages: list) -> str:
    # Try primary model
    try:
        response = await call_anthropic(messages, model="claude-sonnet-4-6")
        return response
    except Exception as primary_error:
        log.warning("Primary model failed, trying fallback", error=str(primary_error))
    
    # Fallback to OpenAI
    try:
        response = await call_openai(messages, model="gpt-4o")
        return response
    except Exception as fallback_error:
        log.error("Both models failed", error=str(fallback_error))
    
    # Graceful degradation
    return "I'm temporarily unavailable. Please try again in a moment."
```

## Idempotency for Agent Actions

Prevent duplicate actions if a request is retried:

```python
import hashlib
from redis import Redis

redis = Redis()

def idempotent_action(action_key: str, fn, *args, **kwargs):
    """Execute action only once; return cached result on retry."""
    cache_key = f"idempotent:{action_key}"
    
    if cached := redis.get(cache_key):
        log.info("Returning cached result", action_key=action_key)
        return json.loads(cached)
    
    result = fn(*args, **kwargs)
    redis.setex(cache_key, 86400, json.dumps(result))  # 24 hour TTL
    return result

# Usage — send email only once even if agent retries
idempotent_action(
    f"send_email:{run_id}:{recipient}",
    send_email,
    to=recipient,
    subject="Report Ready",
    body=report_content
)
```

## Context Window Management

```python
class ContextManager:
    def __init__(self, max_tokens: int = 50_000):
        self.max_tokens = max_tokens
    
    def fit_messages(self, messages: list) -> list:
        total = sum(count_tokens(m) for m in messages)
        
        if total <= self.max_tokens:
            return messages
        
        # Strategy: keep system + last N messages + summarize the rest
        system = [m for m in messages if m["role"] == "system"]
        recent = messages[-6:]  # keep last 3 turns
        middle = messages[len(system):-6]
        
        if middle:
            summary = self.summarize(middle)
            summary_msg = {
                "role": "user",
                "content": f"[Earlier conversation summary: {summary}]"
            }
            return system + [summary_msg] + recent
        
        return system + recent
    
    def summarize(self, messages: list) -> str:
        return client.messages.create(
            model="claude-haiku-4-5-20251001",  # cheap model for summarization
            max_tokens=200,
            messages=[
                {"role": "user", "content": f"Summarize in 100 words: {messages}"}
            ]
        ).content[0].text
```

## Timeouts at Every Layer

```python
import asyncio

async def run_agent_with_timeout(task: str, timeout: float = 30.0) -> str:
    try:
        return await asyncio.wait_for(
            agent.run(task),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return f"Task timed out after {timeout}s. Please try a simpler request."

# Also set per-tool timeouts
async def execute_tool_with_timeout(name: str, input: dict) -> str:
    try:
        return await asyncio.wait_for(
            tools[name](**input),
            timeout=10.0  # 10s max per tool
        )
    except asyncio.TimeoutError:
        return f"Tool {name} timed out. Proceeding with available information."
```

## Health Checks and Readiness

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ready")
async def ready():
    checks = {
        "llm_api": await check_llm_connectivity(),
        "vector_db": await check_vector_db(),
        "redis": await check_redis(),
    }
    all_healthy = all(checks.values())
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }

async def check_llm_connectivity() -> bool:
    try:
        await asyncio.wait_for(
            client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=5,
                messages=[{"role": "user", "content": "hi"}]
            ),
            timeout=5.0
        )
        return True
    except:
        return False
```

## Common Interview Questions

**Q: How do you handle LLM API rate limits in production?**
A: (1) Exponential backoff with jitter on 429 errors, (2) request queuing with rate-aware consumer, (3) token bucket rate limiter to stay under limits, (4) multiple API keys with round-robin, (5) circuit breaker to fail fast when limit is sustained, (6) prioritize user-facing over background tasks.

**Q: How would you make an agent resumable after a crash?**
A: Checkpoint agent state after every step to durable storage (Postgres, Redis). Include: messages, tool call history, iteration count, intermediate results. On restart, load checkpoint and continue from last completed step. LangGraph's checkpointing does this out of the box.

**Q: How do you test reliability of an agent in staging?**
A: (1) Chaos testing — randomly fail tools with configured probability, (2) latency injection — add delays to simulate slow APIs, (3) load testing — concurrent agent runs to find rate limit and performance cliffs, (4) edge case suite — empty results, very long context, malformed tool outputs.
