# Coding Interview Questions — Agentic AI

## Question 1: Implement a ReAct Agent from Scratch

**Task**: Build a minimal ReAct agent using the Anthropic SDK with search and calculator tools.

```python
import anthropic
import json
import re

client = anthropic.Anthropic()

# --- Tools ---
def web_search(query: str) -> str:
    # Mock — replace with real search API
    return f"Search results for '{query}': [Result 1: ...] [Result 2: ...]"

def calculator(expression: str) -> str:
    try:
        # Safe eval: only allow math operations
        allowed = set('0123456789+-*/()., ')
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters in expression"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

TOOLS = {
    "web_search": web_search,
    "calculator": calculator,
}

TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": "Search the web for current information. Use for facts, news, data.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "calculator",
        "description": "Evaluate math expressions. Use for any calculations.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression, e.g. '2 + 2 * 10'"}},
            "required": ["expression"]
        }
    }
]

# --- Agent Loop ---
def run_agent(user_query: str, max_iterations: int = 10) -> str:
    messages = [{"role": "user", "content": user_query}]
    
    for iteration in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="You are a helpful assistant. Use tools when you need to look things up or calculate.",
            tools=TOOL_DEFINITIONS,
            messages=messages
        )
        
        # Final answer — no tool calls
        if response.stop_reason == "end_turn":
            return response.content[0].text
        
        # Tool use
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_fn = TOOLS.get(block.name)
                    if tool_fn:
                        result = tool_fn(**block.input)
                    else:
                        result = f"Unknown tool: {block.name}"
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            
            messages.append({"role": "user", "content": tool_results})
        else:
            break
    
    return "Max iterations reached. Unable to complete task."

# Test
if __name__ == "__main__":
    result = run_agent("What is 15% of the current price of Apple stock?")
    print(result)
```

---

## Question 2: Build a Simple RAG Pipeline

**Task**: Implement a basic RAG system — ingest documents, retrieve relevant chunks, answer questions.

```python
import anthropic
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

client = anthropic.Anthropic()

# Initialize ChromaDB
chroma_client = chromadb.Client()
embedding_fn = OpenAIEmbeddingFunction(
    api_key="your-key",
    model_name="text-embedding-3-small"
)
collection = chroma_client.create_collection(
    name="docs",
    embedding_function=embedding_fn
)

# --- Ingestion ---
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def ingest_document(doc_id: str, text: str, metadata: dict = None):
    chunks = chunk_text(text)
    collection.add(
        documents=chunks,
        ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
        metadatas=[{"doc_id": doc_id, **(metadata or {})}] * len(chunks)
    )
    print(f"Ingested {len(chunks)} chunks from {doc_id}")

# --- Retrieval ---
def retrieve(query: str, k: int = 3) -> list[str]:
    results = collection.query(
        query_texts=[query],
        n_results=k
    )
    return results["documents"][0]

# --- Generation ---
def rag_answer(question: str) -> str:
    chunks = retrieve(question, k=3)
    context = "\n\n---\n\n".join(chunks)
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=f"""Answer the question using ONLY the provided context.
If the context doesn't contain the answer, say "I don't have enough information."

Context:
{context}""",
        messages=[{"role": "user", "content": question}]
    )
    
    return response.content[0].text

# Test
if __name__ == "__main__":
    ingest_document("doc1", "Python was created by Guido van Rossum and first released in 1991...")
    answer = rag_answer("Who created Python?")
    print(answer)
```

---

## Question 3: Implement Conversation Memory

**Task**: Build a memory system that persists user preferences across conversations.

```python
import json
from datetime import datetime
import chromadb
import anthropic

client = anthropic.Anthropic()
chroma_client = chromadb.Client()
memory_collection = chroma_client.get_or_create_collection("user_memory")

# --- Memory Operations ---
def save_memory(user_id: str, content: str, memory_type: str):
    memory_id = f"{user_id}_{datetime.now().timestamp()}"
    memory_collection.add(
        documents=[content],
        ids=[memory_id],
        metadatas=[{
            "user_id": user_id,
            "type": memory_type,
            "timestamp": datetime.now().isoformat()
        }]
    )

def recall_memories(user_id: str, query: str, k: int = 5) -> list[str]:
    results = memory_collection.query(
        query_texts=[query],
        where={"user_id": user_id},
        n_results=k
    )
    return results["documents"][0] if results["documents"] else []

def extract_and_save_memories(user_id: str, conversation: str):
    """Use LLM to extract memorable facts from conversation."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"""Extract important facts about the user from this conversation.
Output as JSON array: [{{"type": "preference|fact|goal", "content": "..."}}]
Only include genuinely useful long-term information. Return [] if nothing notable.

Conversation:
{conversation}"""
        }]
    )
    
    try:
        memories = json.loads(response.content[0].text)
        for memory in memories:
            save_memory(user_id, memory["content"], memory["type"])
        return memories
    except json.JSONDecodeError:
        return []

# --- Memory-Augmented Chat ---
def chat_with_memory(user_id: str, user_message: str, history: list) -> str:
    # Recall relevant memories
    memories = recall_memories(user_id, user_message, k=5)
    memory_block = "\n".join(f"- {m}" for m in memories) if memories else "No relevant memories."
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=f"""You are a personalized assistant.

What you remember about this user:
{memory_block}

Use this context naturally — don't mention that you're reading from memory.""",
        messages=history + [{"role": "user", "content": user_message}]
    )
    
    assistant_reply = response.content[0].text
    
    # Extract and save new memories after conversation
    conversation_text = f"User: {user_message}\nAssistant: {assistant_reply}"
    extract_and_save_memories(user_id, conversation_text)
    
    return assistant_reply

# Test
if __name__ == "__main__":
    user_id = "user_123"
    history = []
    
    reply1 = chat_with_memory(user_id, "I prefer Python over JavaScript", history)
    history += [
        {"role": "user", "content": "I prefer Python over JavaScript"},
        {"role": "assistant", "content": reply1}
    ]
    
    reply2 = chat_with_memory(user_id, "What language should I use for my next project?", history)
    print(reply2)  # Should mention Python preference
```

---

## Question 4: Build a Parallel Tool Executor

**Task**: Execute multiple tool calls in parallel for an agent that returns parallel tool calls.

```python
import asyncio
import anthropic
from anthropic.types import ToolUseBlock

client = anthropic.AsyncAnthropic()

async def execute_tool(name: str, input: dict) -> str:
    """Simulates async tool execution."""
    await asyncio.sleep(0.1)  # simulate I/O
    if name == "get_weather":
        return f"Weather in {input['city']}: 72°F, sunny"
    elif name == "get_time":
        from datetime import datetime
        return f"Current time in {input['timezone']}: {datetime.now()}"
    return f"Unknown tool: {name}"

async def run_parallel_agent(query: str) -> str:
    messages = [{"role": "user", "content": query}]
    
    for _ in range(10):  # max iterations
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=[
                {
                    "name": "get_weather",
                    "description": "Get weather for a city.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"]
                    }
                },
                {
                    "name": "get_time",
                    "description": "Get current time in a timezone.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"timezone": {"type": "string"}},
                        "required": ["timezone"]
                    }
                }
            ],
            messages=messages
        )
        
        if response.stop_reason == "end_turn":
            return next(b.text for b in response.content if hasattr(b, "text"))
        
        tool_uses = [b for b in response.content if isinstance(b, ToolUseBlock)]
        
        if not tool_uses:
            break
        
        messages.append({"role": "assistant", "content": response.content})
        
        # Execute ALL tool calls in parallel
        results = await asyncio.gather(
            *[execute_tool(tu.name, tu.input) for tu in tool_uses]
        )
        
        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": result
            }
            for tu, result in zip(tool_uses, results)
        ]
        
        messages.append({"role": "user", "content": tool_results})
    
    return "Unable to complete"

if __name__ == "__main__":
    result = asyncio.run(
        run_parallel_agent("What's the weather in NYC and the time in Tokyo?")
    )
    print(result)
```

---

## What Interviewers Look For

| Skill | What to Demonstrate |
|---|---|
| Agent loop | Correct message structure, stop_reason handling |
| Tool design | Clear descriptions, proper schemas, error returns |
| Reliability | Max iterations, error handling, timeouts |
| Efficiency | Parallel calls, prompt caching awareness |
| Safety | Input validation, no shell injection, permission checks |
| Code quality | Type hints, clean structure, no magic numbers |
