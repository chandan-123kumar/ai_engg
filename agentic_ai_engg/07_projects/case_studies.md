# Real-World Agent Case Studies

## Case Study 1: GitHub Copilot Workspace

**What it is**: Agentic coding assistant that takes a GitHub issue and produces a complete code change.

**Architecture**:
1. Reads issue + codebase context
2. Generates a plan (files to change + why)
3. Implements changes file by file
4. Runs tests, fixes failures
5. Opens PR with description

**Key decisions**:
- Tree-sitter parsing for code understanding (not raw text)
- File-level context management (can't fit entire repo in context)
- Iterative refinement: runs tests, sees failures, fixes
- Human review required before merge (not fully autonomous)

**Interview relevance**: "How would you design a coding agent?" — mention this architecture.

---

## Case Study 2: Anthropic's Claude for Computer Use

**What it is**: Claude can control a computer — see the screen, click, type — to complete tasks.

**Architecture**:
```
User instruction
    ↓
Claude sees screenshot (multimodal input)
    ↓
Decides action: click(x,y) | type(text) | scroll | key(...)
    ↓
Computer executes action
    ↓
New screenshot → Claude sees result
    ↓
[Loop until task complete]
```

**Key challenges**:
- Latency: screenshot → LLM → action → screenshot is slow (2-5s per step)
- Error recovery: misclicks, wrong windows, unexpected dialogs
- Safety: agent can access anything on the computer — huge attack surface
- Context: how to compress visual history (can't keep 100 screenshots in context)

**Interview relevance**: Computer use agents represent the frontier of agentic systems.

---

## Case Study 3: Devin (Cognition AI)

**What it is**: Fully autonomous software engineer — given a task, Devin writes code, runs tests, debugs, and deploys.

**Architecture**:
- Long-horizon planning: breaks tasks into subtasks
- Persistent workspace: uses a real computer (terminal, browser, IDE)
- Memory: stores notes and observations in files
- Self-evaluation: runs tests, checks outputs, loops until passing

**Key decisions**:
- Separate planning model from execution model
- File-based memory (notes.txt) instead of vector store — simpler, more reliable
- Human collaboration: can ask for clarification when blocked

**Interview relevance**: Shows what's possible with agentic systems; raises questions about autonomy vs. oversight.

---

## Case Study 4: Perplexity AI

**What it is**: Search agent that answers questions with real-time web search and citations.

**Architecture**:
```
User Query
    ↓
Query expansion (generate 3 search queries)
    ↓
Parallel web search (all queries simultaneously)
    ↓
Reranking (select most relevant results)
    ↓
Content extraction (scrape key text)
    ↓
Synthesis (answer with inline citations)
    ↓
Follow-up suggestions
```

**Key decisions**:
- Query expansion: 1 query often misses context; 3 parallel queries cover more ground
- Fast model for query expansion (Haiku), larger for synthesis (Sonnet)
- Citation tracking: maintain source → text mapping throughout pipeline
- Streaming: start generating answer before all sources are read

**Interview relevance**: Production RAG system at scale — cite as evidence that RAG > long-context stuffing for search.

---

## Case Study 5: AutoGPT / BabyAGI (Lessons Learned)

**What they were**: Early autonomous agents (2023) that could set their own sub-tasks and run indefinitely.

**Why they largely failed in practice**:
1. **Infinite loops**: no hard termination conditions
2. **Goal drift**: agent would go off-task over many iterations
3. **Error compounding**: each mistake made subsequent steps worse
4. **No evaluation**: agent couldn't tell if it was making progress
5. **Cost explosion**: 100s of LLM calls for simple tasks

**What they taught us**:
- Agents need hard limits (iterations, tokens, time)
- Human checkpoints are essential for long-horizon tasks
- Evaluation at each step prevents error compounding
- Simpler is better: most tasks don't need 50 agent steps

**Interview relevance**: Know this history — shows you understand the field's evolution.

---

## Common Patterns Across Case Studies

| Pattern | Companies using it |
|---|---|
| Parallel tool calls | Perplexity, GitHub Copilot |
| Hierarchical planning | Devin, GitHub Copilot Workspace |
| Human checkpoints | GitHub Copilot, Claude Computer Use |
| Iterative refinement with tests | Devin, SWE-agent |
| Multi-model routing | Perplexity (fast + slow) |
| Streaming for UX | Perplexity, Claude, ChatGPT |
| Self-evaluation loops | Devin, Reflexion-based systems |

## Key Takeaways for Interviews

1. **Real agents need safety mechanisms** — every production agent has guardrails and human oversight
2. **Latency is the #1 UX concern** — parallelism, streaming, and caching are core, not optional
3. **Evaluation is non-negotiable** — every company has offline eval suites; this is a differentiator
4. **Simple first** — most production agents are simpler than they appear; complexity is added incrementally
5. **Cost matters at scale** — every architecture decision has a cost implication; always think about it
