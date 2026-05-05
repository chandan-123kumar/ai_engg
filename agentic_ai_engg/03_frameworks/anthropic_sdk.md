# Anthropic SDK — Interview Guide

## Core SDK Usage

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.content[0].text)
```

## Message Structure
```python
# Multi-turn conversation
messages = [
    {"role": "user", "content": "What's 2+2?"},
    {"role": "assistant", "content": "4."},
    {"role": "user", "content": "Multiply that by 5."},
]
```

## Tool Use (Function Calling)

```python
tools = [
    {
        "name": "get_stock_price",
        "description": "Get current stock price for a ticker symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker, e.g. AAPL"}
            },
            "required": ["ticker"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's Apple's stock price?"}]
)

# Handle tool use
if response.stop_reason == "tool_use":
    for block in response.content:
        if block.type == "tool_use":
            tool_name = block.name
            tool_input = block.input
            tool_use_id = block.id
            
            # Execute tool
            result = execute_tool(tool_name, tool_input)
            
            # Feed result back
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": str(result)
                }]
            })
```

## Prompt Caching (Critical for Cost)

Caching saves K/V computed for static content — reused on subsequent calls.

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert Python developer.",
        },
        {
            "type": "text",
            "text": LARGE_CODEBASE_CONTEXT,  # e.g., 50k token codebase
            "cache_control": {"type": "ephemeral"}  # cache this
        }
    ],
    messages=[{"role": "user", "content": "Explain the main function."}]
)

# Check cache usage
print(response.usage.cache_creation_input_tokens)  # tokens cached this call
print(response.usage.cache_read_input_tokens)       # tokens read from cache
```

**Cost impact**: cached tokens cost ~10% of normal input tokens. For a 100k-token system prompt read 100 times: 90% cost reduction.

**Cache TTL**: 5 minutes (ephemeral). Persist by making a call within 5 minutes.

**When to cache**: system prompt, large document context, tool definitions, few-shot examples.

## Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a poem."}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Get final message after stream
final_message = stream.get_final_message()
```

## Extended Thinking (claude-opus-4-7+)

```python
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000  # how much to think before answering
    },
    messages=[{"role": "user", "content": "Solve this hard math problem..."}]
)

for block in response.content:
    if block.type == "thinking":
        print("Thinking:", block.thinking)
    elif block.type == "text":
        print("Answer:", block.text)
```

Use for: complex reasoning, multi-step math, hard coding problems. Costs ~3× more.

## Vision (Multimodal)

```python
import base64

with open("diagram.png", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data,
                }
            },
            {"type": "text", "text": "Explain this architecture diagram."}
        ]
    }]
)
```

## Batch API (Async, High Volume)

```python
# Submit batch
batch = client.beta.messages.batches.create(
    requests=[
        {
            "custom_id": f"request-{i}",
            "params": {
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 256,
                "messages": [{"role": "user", "content": doc}]
            }
        }
        for i, doc in enumerate(documents)
    ]
)

# Poll for completion (or use webhook)
import time
while True:
    batch = client.beta.messages.batches.retrieve(batch.id)
    if batch.processing_status == "ended":
        break
    time.sleep(60)

# Get results
for result in client.beta.messages.batches.results(batch.id):
    print(result.custom_id, result.result.message.content[0].text)
```

**50% cost discount vs real-time API. 24-hour processing window.**

## Model Selection Guide

| Model | When to use | Cost |
|---|---|---|
| claude-haiku-4-5 | Simple tasks, high volume, latency-sensitive | Cheapest |
| claude-sonnet-4-6 | Most production agent tasks | Mid |
| claude-opus-4-7 | Complex reasoning, hard coding, agentic | Most expensive |

## Common Interview Questions

**Q: How do you implement prompt caching for an agent with a large knowledge base?**
A: Put the knowledge base text in the system message with `cache_control: {"type": "ephemeral"}`. Ensure all requests within 5 minutes reuse the same cache block. Track `cache_read_input_tokens` in usage metrics to verify cache is hitting. Can reduce costs by 80–90% for knowledge-heavy agents.

**Q: How does streaming improve agent UX?**
A: User sees partial responses as they're generated instead of waiting for the full response. For agents, stream at the final answer generation step. For intermediate tool calls (which are JSON), streaming is less valuable — users don't need to see half-formed JSON.

**Q: When would you use the Batch API?**
A: Offline processing tasks: document classification, data enrichment, embedding generation, nightly report generation. Not for real-time user interactions. 50% cost savings make it compelling for high-volume background jobs.
