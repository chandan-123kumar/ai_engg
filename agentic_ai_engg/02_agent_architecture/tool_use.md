# Tool Use — Interview Guide

## What is Tool Use?

Tool use (function calling) allows an LLM to request execution of external functions. The LLM outputs a structured call; the application executes it; results are fed back to the LLM.

```
LLM → { "tool": "search", "input": "weather in NYC" }
App → executes search("weather in NYC")
App → returns "72°F, partly cloudy"
LLM → "The weather in NYC is 72°F and partly cloudy."
```

The LLM never directly executes code — it only requests calls.

## Tool Definition (OpenAI/Anthropic Format)

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city. Use when user asks about weather.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'New York'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["city"]
        }
    }
]
```

**Description quality matters enormously** — the LLM decides which tool to call based on the description. Be specific about WHEN to use each tool.

## Implementing Tool Use with Anthropic SDK

```python
import anthropic

client = anthropic.Anthropic()

def run_agent(user_message: str):
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        # Check stop reason
        if response.stop_reason == "end_turn":
            return response.content[0].text
        
        if response.stop_reason == "tool_use":
            # Extract tool calls
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            
            # Add assistant message with tool calls
            messages.append({"role": "assistant", "content": response.content})
            
            # Execute tools and collect results
            tool_results = []
            for tool_use in tool_uses:
                result = execute_tool(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(result)
                })
            
            # Add tool results back
            messages.append({"role": "user", "content": tool_results})
```

## Parallel Tool Use
Claude and GPT-4 support calling multiple tools in one turn:
```json
[
  {"tool": "search", "input": {"query": "OpenAI revenue"}},
  {"tool": "search", "input": {"query": "Anthropic revenue"}}
]
```
- Run in parallel → faster response
- Significant latency win for independent lookups

## Tool Design Principles

### 1. Single Responsibility
Each tool does one thing. Bad: `manage_database(action, table, data)`. Good: `read_row(table, id)`, `insert_row(table, data)`, `update_row(table, id, data)`.

### 2. Idempotency for Read Tools
Read-only tools should be safe to call multiple times. Mark write tools clearly so the agent (and the safety layer) knows they have side effects.

### 3. Rich Return Values
Return structured data, not just strings:
```python
def search_web(query: str) -> dict:
    return {
        "results": [...],
        "total_found": 142,
        "query_interpreted_as": "...",
    }
```

### 4. Error Messages That Help the LLM
```python
# Bad
raise Exception("Error")

# Good
return {"error": "No results found for 'XYZ'. Try a broader search term or check spelling."}
```

### 5. Timeout and Retry
```python
import httpx

async def call_api_tool(endpoint: str, payload: dict):
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(3):
            try:
                response = await client.post(endpoint, json=payload)
                return response.json()
            except httpx.TimeoutException:
                if attempt == 2:
                    return {"error": "Tool timed out after 3 attempts"}
```

## Common Tool Categories

| Category | Examples | Notes |
|---|---|---|
| Search | Web search, vector DB, SQL | Read-only, always safe |
| Code execution | Python REPL, bash | Sandboxed; highest risk |
| APIs | Weather, calendar, CRM | Rate limits, auth needed |
| File ops | Read, write, list files | Scope to allowed paths only |
| Communication | Email, Slack, SMS | Irreversible; require confirmation |
| Browser | Click, type, screenshot | Playwright/Puppeteer based |

## Safety Considerations

### Principle of Least Privilege
Only give agents the tools they need for the task. A customer support agent doesn't need `delete_database`.

### Human-in-the-Loop for Irreversible Actions
```python
REQUIRES_CONFIRMATION = {"send_email", "delete_file", "charge_card"}

def execute_tool(name: str, input: dict):
    if name in REQUIRES_CONFIRMATION:
        confirmed = ask_user(f"Confirm: {name}({input})?")
        if not confirmed:
            return {"status": "cancelled by user"}
    return tools[name](**input)
```

### Input Validation
```python
from pydantic import BaseModel, validator

class SearchInput(BaseModel):
    query: str
    max_results: int = 5
    
    @validator("query")
    def no_injection(cls, v):
        if any(c in v for c in [";", "--", "DROP"]):
            raise ValueError("Invalid query")
        return v
```

## Common Interview Questions

**Q: How does function calling differ from regular prompting?**
A: In regular prompting, the LLM outputs free text that you parse. In function calling, the LLM outputs structured JSON against a schema you defined, and the API enforces the schema. More reliable for downstream parsing and prevents format drift.

**Q: How would you design a tool for a code execution agent?**
A: Sandboxed environment (Docker/subprocess with resource limits), timeout (5–30s), limited filesystem access (tmp dir only), no network unless needed, capture stdout/stderr/return code, return structured result. Never allow shell=True with user input.

**Q: An agent calls a tool that fails. How do you handle it?**
A: Return a descriptive error message to the LLM (don't raise, don't crash). Include what failed and suggested next steps. The LLM can then retry with different parameters or use a fallback tool. Log the error for observability.

**Q: How do you prevent tool call loops (e.g., search → search → search)?**
A: (1) Track tool call history in state, (2) detect repeated calls with same input, (3) limit total tool calls per turn, (4) prompt the agent to stop searching and answer with best available info after N attempts.
