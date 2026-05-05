# Observability — Interview Guide

## Why Observability is Critical for Agents

Agents are non-deterministic, multi-step, and stateful. Without observability you can't:
- Debug why an agent failed or gave a wrong answer
- Measure latency and cost per step
- Detect regressions after model updates
- Audit what actions were taken

## Key Metrics to Track

### Performance Metrics
```python
@dataclass
class AgentRunMetrics:
    run_id: str
    user_id: str
    task: str
    
    # Latency
    total_latency_ms: float
    llm_latency_ms: float       # time waiting for LLM
    tool_latency_ms: float      # time in tool calls
    
    # Token usage
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    
    # Cost
    total_cost_usd: float
    
    # Quality
    num_steps: int
    num_tool_calls: int
    success: bool
    error: str | None
```

### LLM-Specific Metrics
```python
def track_llm_call(response):
    metrics.record({
        "model": response.model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_read_input_tokens": response.usage.cache_read_input_tokens,
        "stop_reason": response.stop_reason,
        "latency_ms": elapsed_ms,
    })
```

## Distributed Tracing for Agents

Each agent run should have a **trace** — a tree of spans showing every step:

```
trace_id: abc-123
├── span: agent_run (500ms)
│   ├── span: llm_call_1 (200ms) [input: 2k tokens, output: 150 tokens]
│   ├── span: tool_call: search_web (100ms) [query: "..."]
│   ├── span: llm_call_2 (180ms) [input: 3k tokens, output: 300 tokens]
│   └── span: tool_call: write_file (20ms) [path: "output.txt"]
```

### Implementation with OpenTelemetry
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer("agent")

def agent_step(state: AgentState) -> AgentState:
    with tracer.start_as_current_span("agent_step") as span:
        span.set_attribute("iteration", state.iterations)
        span.set_attribute("input_tokens", estimate_tokens(state.messages))
        
        response = llm.invoke(state.messages)
        
        span.set_attribute("output_tokens", response.usage.output_tokens)
        span.set_attribute("stop_reason", response.stop_reason)
        
        return update_state(state, response)
```

## LangSmith (LangChain Observability)

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-key"
os.environ["LANGCHAIN_PROJECT"] = "my-agent"

# Now all LangChain/LangGraph calls are automatically traced
# View traces at smith.langchain.com
```

LangSmith captures:
- Full prompt + response for every LLM call
- Tool calls and results
- Latency per step
- Token usage and cost
- Error traces

## Logging Strategy

### Structured Logging
```python
import structlog

log = structlog.get_logger()

def execute_tool(name: str, input: dict, run_id: str):
    log.info("tool.start", tool=name, run_id=run_id, input_keys=list(input.keys()))
    
    start = time.time()
    try:
        result = tools[name](**input)
        log.info("tool.success", tool=name, run_id=run_id, 
                 latency_ms=(time.time()-start)*1000)
        return result
    except Exception as e:
        log.error("tool.error", tool=name, run_id=run_id, error=str(e))
        raise
```

### What to Log
```python
LOG_AGENT_RUN = {
    "run_id": "uuid",
    "user_id": "hashed",          # anonymize PII
    "task_category": "summarize", # not the raw task (may have PII)
    "model": "claude-sonnet-4-6",
    "num_steps": 4,
    "success": True,
    "total_tokens": 5420,
    "total_cost_usd": 0.021,
    "latency_ms": 3200,
    "tools_used": ["search_web", "write_file"],
}
```

## Alerting

```python
# Set up alerts for:
ALERT_THRESHOLDS = {
    "error_rate_pct": 5,          # >5% of runs fail
    "avg_latency_ms": 10_000,     # avg > 10 seconds
    "p99_latency_ms": 30_000,     # p99 > 30 seconds
    "cost_per_run_usd": 0.50,     # individual run > $0.50
    "daily_cost_usd": 100,        # total daily cost > $100
    "token_budget_exceeded": True, # any run hit token limit
}
```

## Cost Monitoring

```python
COST_PER_TOKEN = {
    "claude-sonnet-4-6": {
        "input": 3.00 / 1_000_000,
        "output": 15.00 / 1_000_000,
        "cache_read": 0.30 / 1_000_000,   # 90% discount
        "cache_write": 3.75 / 1_000_000,  # 25% premium on first write
    }
}

def calculate_cost(usage) -> float:
    rates = COST_PER_TOKEN["claude-sonnet-4-6"]
    return (
        usage.input_tokens * rates["input"] +
        usage.output_tokens * rates["output"] +
        usage.cache_read_input_tokens * rates["cache_read"] +
        usage.cache_creation_input_tokens * rates["cache_write"]
    )
```

## Common Interview Questions

**Q: How do you debug an agent that gives wrong answers intermittently?**
A: (1) Capture full traces for failing runs (full prompt + response at each step), (2) compare token-by-token where the failing run diverges from successful runs, (3) check if tool calls returned unexpected data, (4) look at iteration count — loops indicate the agent got confused, (5) reproduce deterministically with temperature=0 and the exact captured messages.

**Q: What's the most important metric for a production agent?**
A: Task success rate — did it actually solve the user's problem. Secondary: latency (user experience) and cost per successful task (unit economics). Error rate is a leading indicator. If success rate drops, investigate error logs + traces from failing runs.

**Q: How would you set up alerting for an agent in production?**
A: (1) Error rate > threshold → PagerDuty, (2) latency p99 spike → ops alert, (3) daily cost anomaly → Slack, (4) specific error patterns (tool failures, context overflow) → categorized alerts with runbooks. Use time-windowed rolling averages to avoid false positives from momentary spikes.
