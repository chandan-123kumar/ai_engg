# Latency & Cost Optimization — Interview Guide

## Latency Breakdown for a Typical Agent Turn

```
User sends message
    ↓ (network: ~50ms)
Embed query (for RAG: ~50ms)
    ↓
Vector store retrieval (~20-100ms)
    ↓
LLM API call — TTFT (time-to-first-token: 500ms–3s)
    ↓
LLM generation — streaming (~30 tokens/sec for Sonnet)
    ↓
Tool execution (if needed: 100ms–2s)
    ↓
Second LLM call (if tool called: 500ms–2s)
    ↓
Response to user

Total: 1–10 seconds per turn (multi-step agents: multiply per step)
```

## Latency Optimization Strategies

### 1. Prompt Caching
```python
# Without caching: every call re-processes 50k token system prompt
# With caching: only new tokens processed after first call

system = [
    {"type": "text", "text": agent_persona},
    {
        "type": "text",
        "text": large_knowledge_base,  # 50k tokens
        "cache_control": {"type": "ephemeral"}
    }
]
# First call: full processing (2-3s)
# Subsequent calls: cache hit, 90% faster
```

**Impact**: reduces TTFT by 50–90% for prompts with large static content.

### 2. Streaming
Show results as they generate — perceived latency much lower:
```python
async def stream_response(messages):
    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=messages
    ) as stream:
        async for text in stream.text_stream:
            yield text  # send to frontend immediately
```

### 3. Parallel Tool Calls
```python
import asyncio

async def execute_parallel_tools(tool_calls: list[ToolCall]) -> list:
    tasks = [execute_tool_async(tc.name, tc.input) for tc in tool_calls]
    return await asyncio.gather(*tasks)

# 3 sequential tool calls × 500ms = 1500ms
# 3 parallel tool calls = ~500ms + overhead
```

### 4. Model Routing (Cascade)
Use cheap/fast model for simple tasks, expensive model only when needed:
```python
async def route_to_model(task: str) -> str:
    complexity = assess_complexity(task)  # simple heuristic
    
    if complexity == "simple":
        model = "claude-haiku-4-5-20251001"  # 50ms, $0.001
    elif complexity == "medium":
        model = "claude-sonnet-4-6"           # 500ms, $0.01
    else:
        model = "claude-opus-4-7"             # 2s, $0.05
    
    return model
```

### 5. Response Caching
Cache identical or semantically similar queries:
```python
import hashlib
from functools import lru_cache

def cache_key(messages: list, model: str) -> str:
    content = str(messages) + model
    return hashlib.sha256(content.encode()).hexdigest()

async def cached_llm_call(messages, model):
    key = cache_key(messages, model)
    if cached := redis.get(key):
        return json.loads(cached)
    
    response = await llm.invoke(messages, model=model)
    redis.setex(key, 3600, json.dumps(response))  # 1 hour TTL
    return response
```

### 6. Prefetching
Start the LLM call before the user finishes typing (speculative execution):
- Embed user input as they type
- Pre-fetch likely documents
- Start LLM warm-up on the first few tokens of input

## Cost Optimization Strategies

### Token Budget Management
```python
MAX_CONTEXT_TOKENS = 20_000  # budget per agent run

def trim_messages(messages: list, max_tokens: int) -> list:
    total = 0
    trimmed = []
    
    # Always keep system message and last user message
    for msg in reversed(messages):
        tokens = count_tokens(msg)
        if total + tokens > max_tokens and len(trimmed) > 2:
            break
        trimmed.insert(0, msg)
        total += tokens
    
    return trimmed
```

### Choosing the Right Model
```python
TASK_MODEL_MAP = {
    "intent_classification": "claude-haiku-4-5-20251001",  # binary output
    "entity_extraction": "claude-haiku-4-5-20251001",      # structured output
    "summarization": "claude-sonnet-4-6",                   # quality matters
    "code_generation": "claude-sonnet-4-6",                 # balance
    "complex_reasoning": "claude-opus-4-7",                 # only when needed
}
```

### Batch API for Offline Workloads
```python
# Real-time: $3/M tokens
# Batch API: $1.50/M tokens (50% off)

# Use batch for:
# - Nightly document processing
# - Bulk classification
# - Embedding generation
# - Report generation
```

### Output Length Control
```python
# Be explicit about expected output length
prompts = {
    "short": "Respond in one sentence.",
    "medium": "Respond in 2-3 sentences.",
    "structured": "Respond in JSON only, no explanation.",
}

# max_tokens should match expected output
# Don't set max_tokens=4096 if you expect 50-token responses
```

## Cost Calculator

```python
def estimate_agent_cost(
    num_turns: int,
    avg_input_tokens_per_turn: int,
    avg_output_tokens_per_turn: int,
    model: str = "claude-sonnet-4-6",
    cache_ratio: float = 0.7  # 70% of input from cache
) -> dict:
    rates = {
        "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_read": 0.30},
        "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0, "cache_read": 0.08},
        "claude-opus-4-7": {"input": 15.0, "output": 75.0, "cache_read": 1.50},
    }[model]
    
    per_turn_cost = (
        (avg_input_tokens_per_turn * (1 - cache_ratio)) / 1e6 * rates["input"] +
        (avg_input_tokens_per_turn * cache_ratio) / 1e6 * rates["cache_read"] +
        avg_output_tokens_per_turn / 1e6 * rates["output"]
    )
    
    return {
        "per_turn_usd": per_turn_cost,
        "total_usd": per_turn_cost * num_turns,
        "per_1000_conversations": per_turn_cost * num_turns * 1000
    }
```

## Common Interview Questions

**Q: An agent is taking 10 seconds per response. How do you debug and fix it?**
A: (1) Add timing spans per step — identify if latency is in LLM, tool calls, or network. (2) If LLM: enable prompt caching for large system prompts, use streaming for UX, consider a faster model. (3) If tools: parallelize independent tool calls, add timeouts, cache tool results. (4) If context building: limit retrieved chunks, compress history.

**Q: How would you reduce cost by 50% without hurting quality?**
A: (1) Prompt caching (80–90% off for static content), (2) route simple queries to Haiku instead of Sonnet (75% cheaper), (3) reduce max_tokens to match actual output length, (4) use Batch API for async workloads (50% off), (5) cache identical queries for 1 hour. Measure quality at each step to ensure no regression.

**Q: What's the cost of running 1 million agent conversations per day?**
A: Depends heavily on configuration. Example: 3 turns/conversation, 2k input + 300 output tokens each, Sonnet 4.6 with 70% cache hit:
- Input (uncached): 0.6M turns × 600 tokens = 360M tokens × $3/M = $1,080
- Input (cached): 0.6M turns × 1400 tokens = 840M tokens × $0.30/M = $252
- Output: 1.8M turns × 300 tokens = 540M tokens × $15/M = $8,100
- **Total ≈ $9,432/day**. Optimize with Haiku for simple turns → 3–5× reduction.
