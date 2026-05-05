# Portfolio Projects for Agentic AI Interviews

## Why Projects Matter

Interviewers at AI companies want to see you've built agents that actually run — not just studied theory. A well-executed project demonstrates:
- You understand the agent loop in practice
- You've dealt with real failure modes
- You can make architecture decisions and explain trade-offs

---

## Project 1: Personal Research Agent ⭐ Beginner

**What it does**: Given a research topic, the agent searches the web, reads pages, synthesizes findings, and outputs a structured report with citations.

**Tech stack**: Anthropic SDK, Tavily/SerpAPI (web search), BeautifulSoup (page parsing)

**Key components**:
- ReAct loop with `web_search` and `read_page` tools
- Context management: summarize search results to avoid overflow
- Citation tracking: map each claim to its source URL
- Output: structured Markdown report

**Interview talking points**:
- How you handled long web page content (summarize before injecting)
- How you prevented the agent from looping on the same queries
- How you validated the quality of the output (faithfulness metric)

**Code skeleton**:
```python
tools = ["web_search", "read_page", "extract_key_points", "write_section"]

# Agent loop: search → read → extract → synthesize → write
# Challenge: content too long → truncate + summarize
# Challenge: duplicate results → dedup by URL
```

---

## Project 2: Code Review Agent ⭐⭐ Intermediate

**What it does**: Takes a Python file or PR diff, analyzes it for bugs, security issues, and style problems, returns structured review comments.

**Tech stack**: Anthropic SDK, GitHub API (gh CLI or PyGitHub), LangGraph

**Key components**:
- Multi-pass analysis: (1) understand code intent, (2) review for bugs, (3) review for security
- Structured output: list of `{file, line, severity, comment}` objects
- GitHub integration: post comments directly to PR

**Interview talking points**:
- Why you used multiple passes (single pass misses issues)
- How you scoped permissions (read-only GitHub access)
- How you evaluated quality (compare to human reviews)

---

## Project 3: Customer Support Agent ⭐⭐ Intermediate

**What it does**: Handles customer queries using a knowledge base (FAQs, product docs), can look up order status, and escalates to humans when needed.

**Tech stack**: Anthropic SDK, ChromaDB (knowledge base), FastAPI, SQLite (mock order DB)

**Key components**:
- RAG for knowledge base retrieval
- Tool: `lookup_order(order_id)` against database
- Escalation: detect frustration/complexity, hand off gracefully
- Guardrails: don't discuss competitors, don't make promises

**Interview talking points**:
- RAG pipeline decisions (chunk size, retrieval k)
- How escalation detection works (LLM classifier)
- What you'd change for production (Postgres, Redis, proper auth)

---

## Project 4: SQL Agent ⭐⭐ Intermediate

**What it does**: Natural language to SQL. User asks a business question in English; agent generates SQL, validates it, executes it, and explains the results.

**Tech stack**: Anthropic SDK, SQLite/Postgres, LangGraph for retry loop

**Key components**:
- Schema preloading in system prompt (with caching)
- SQL validation: parse before execute, read-only user, query timeout
- Auto-retry: if SQL fails, agent sees the error and fixes it
- Result interpretation: translate raw rows to business language

**Interview talking points**:
- Safety: how you prevented DELETE/DROP/INSERT
- Retry loop: LangGraph state machine with fix-and-retry node
- Accuracy: how you measured SQL correctness (Spider benchmark)

---

## Project 5: Multi-Agent Writing System ⭐⭐⭐ Advanced

**What it does**: A crew of specialized agents collaborates to produce a high-quality article: researcher, writer, fact-checker, editor.

**Tech stack**: LangGraph (subgraphs), Anthropic SDK, Tavily search

**Architecture**:
```
Orchestrator
├── Researcher (parallel web searches)
├── Writer (drafts sections in parallel)
├── Fact-Checker (verifies claims)
└── Editor (coherence + polish)
```

**Interview talking points**:
- How you coordinated agents (shared state vs message passing)
- How you measured quality improvement vs. single agent (eval set)
- Cost analysis: multi-agent is 3-5× more expensive — justified?
- How you handled fact-checker disagreements

---

## Project 6: Agentic RAG with Self-Correction ⭐⭐⭐ Advanced

**What it does**: A RAG system where the agent evaluates its own retrieved context and triggers additional retrieval if the initial results are insufficient.

**Tech stack**: LangGraph, ChromaDB, Anthropic SDK, RAGAS for evaluation

**Key components**:
- Initial retrieval + relevance scoring (LLM-based)
- If score < threshold: reformulate query, retrieve again
- Corrective RAG: if no good context found, web search fallback
- Full evaluation with RAGAS metrics

**Interview talking points**:
- CRAG architecture: how the evaluation loop works
- Trade-off: extra LLM calls vs. quality improvement
- Evaluation: faithfulness score before and after self-correction

---

## How to Present Projects in Interviews

### The STAR-A Format
- **Situation**: what problem were you solving?
- **Task**: what did you build?
- **Action**: key technical decisions and why
- **Result**: metrics, outcomes, learnings
- **Alternatives**: what else you considered and why you chose your approach

### Always Prepare
1. What was the hardest technical challenge?
2. What would you do differently?
3. How did you evaluate quality?
4. How would you scale it to 10× users?
5. What safety considerations did you implement?

### GitHub Repo Checklist
- [ ] README with architecture diagram
- [ ] .env.example (never commit real keys)
- [ ] Requirements.txt or pyproject.toml
- [ ] Example input/output in README
- [ ] Eval results or quality metrics mentioned
- [ ] Clear run instructions
