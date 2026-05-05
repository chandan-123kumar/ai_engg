# Memory Systems — Interview Guide

## Types of Agent Memory

```
┌─────────────────────────────────────────────────┐
│              Agent Memory Architecture          │
│                                                 │
│  ┌──────────────┐  ┌──────────────────────────┐ │
│  │   In-Context │  │     External Memory       │ │
│  │   (Working)  │  │                          │ │
│  │              │  │  ┌──────────┐            │ │
│  │  - Messages  │  │  │ Episodic │ Past convs │ │
│  │  - Tool outs │  │  └──────────┘            │ │
│  │  - Scratchpad│  │  ┌──────────┐            │ │
│  │              │  │  │ Semantic │ Facts/docs │ │
│  └──────────────┘  │  └──────────┘            │ │
│                    │  ┌──────────┐            │ │
│                    │  │Procedural│ Skills/how │ │
│                    │  └──────────┘            │ │
│                    └──────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## 1. In-Context (Working) Memory

The agent's context window — everything visible right now.

**What goes here:**
- System prompt (persona, tools, rules)
- Conversation history
- Tool call results
- Current scratchpad

**Limits:**
- Finite (32k–200k tokens)
- Lost when context is cleared
- Expensive (every token costs money)

**Management strategies:**
```python
class ContextManager:
    def compress_history(self, messages: list, max_tokens: int):
        # Keep recent messages + summarize older ones
        recent = messages[-10:]
        older = messages[:-10]
        
        if not older:
            return recent
            
        summary = llm.invoke(
            f"Summarize these past messages in 100 words:\n{older}"
        )
        return [{"role": "system", "content": f"Summary: {summary}"}] + recent
```

## 2. Episodic Memory (Past Conversations)

Stores what happened in previous sessions.

**Use cases:**
- "Remember last week you helped me with X..."
- Personalization across sessions
- Debugging agent failures

**Implementation:**
```python
import chromadb
from datetime import datetime

class EpisodicMemory:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("episodes")
    
    def save_episode(self, conversation: list, user_id: str):
        summary = llm.invoke(f"Summarize this conversation: {conversation}")
        self.collection.add(
            documents=[summary],
            metadatas=[{"user_id": user_id, "timestamp": datetime.now().isoformat()}],
            ids=[f"{user_id}_{datetime.now().timestamp()}"]
        )
    
    def recall(self, query: str, user_id: str, k: int = 3):
        return self.collection.query(
            query_texts=[query],
            where={"user_id": user_id},
            n_results=k
        )
```

## 3. Semantic Memory (Knowledge Base)

Stores facts, documents, domain knowledge — the agent's "long-term knowledge."

**This is RAG** — see `rag_fundamentals.md` for full detail.

Key point: semantic memory retrieval should be triggered by the agent itself, not hardcoded.

```python
tools = [
    {
        "name": "search_knowledge_base",
        "description": "Search company knowledge base for product info, policies, or FAQs. Use when you need specific factual information.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}
    }
]
```

## 4. Procedural Memory (Skills)

How to perform tasks — stored as:
- **Prompts**: few-shot examples of correct procedure
- **Code tools**: executable functions
- **Fine-tuning**: baked into model weights

Example: an agent learns that "when user asks to draft an email, always ask for recipient and subject first before drafting" — this is procedural knowledge.

## Memory Write Strategies

### When to Save
```python
MEMORY_TRIGGERS = [
    "user preference",      # "I prefer Python over JavaScript"
    "user correction",      # "No, that's not right. The policy is..."
    "task completion",      # log successful strategies
    "explicit instruction", # "Remember that..."
]
```

### Structured Memory Format
```python
@dataclass
class Memory:
    content: str
    type: str           # episodic | semantic | procedural
    source: str         # conversation, tool, user
    timestamp: datetime
    importance: float   # 0–1, used for eviction
    user_id: str
    tags: list[str]
```

## Memory Retrieval Patterns

### Retrieval-Augmented Memory
At the start of each turn:
1. Embed the user's message
2. Query memory store for relevant memories
3. Inject top-K memories into system prompt
4. Proceed with enriched context

```python
def build_prompt_with_memory(user_message: str, user_id: str) -> str:
    memories = memory_store.recall(user_message, user_id, k=5)
    memory_block = "\n".join(f"- {m}" for m in memories)
    
    return f"""
You are a helpful assistant.

Relevant context from previous conversations:
{memory_block}

Current conversation:
{user_message}
"""
```

### Memory Consolidation
- Periodically summarize and compress episodic memories
- Extract semantic facts from episodes
- Remove duplicates, update contradictions

```python
def consolidate_memories(user_id: str):
    episodes = episodic_memory.get_all(user_id)
    facts = llm.invoke(f"Extract key facts about this user from: {episodes}")
    semantic_memory.upsert(user_id, facts)
    episodic_memory.archive_old(user_id, days=30)
```

## Common Interview Questions

**Q: How does an agent maintain context across multiple conversations?**
A: External memory stores (vector DB for semantic similarity retrieval, or key-value for exact lookup). At session start, retrieve relevant past context and inject into system prompt. The agent can also explicitly store information using a `remember` tool.

**Q: What is the difference between episodic and semantic memory?**
A: Episodic = specific past events ("Last Tuesday I debugged a Python import error"). Semantic = general facts and knowledge ("Python uses 0-based indexing"). Agents need both: episodic for personalization/continuity, semantic for domain knowledge.

**Q: How would you implement memory for a customer support agent?**
A: (1) Episodic: store past tickets per user (retrieve on new ticket), (2) Semantic: company knowledge base via RAG, (3) Procedural: escalation procedures in system prompt, (4) Working: current ticket context in context window. Prioritize recency and relevance for retrieval.

**Q: What is the "memory palace" problem in agents?**
A: When agents have too much retrieved memory, they get confused by irrelevant or contradictory information. Solutions: selective retrieval (high relevance threshold), memory ranking by recency × relevance, structured memory with clear categories.
