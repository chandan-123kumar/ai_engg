# System Design Interview Questions — Agentic AI

## How to Approach Agentic System Design

Use this framework for every question:
1. **Clarify scope** — single user or multi-tenant? real-time or async? what's the SLA?
2. **Define components** — LLM, tools, memory, orchestration
3. **Draw the flow** — request → agent loop → response
4. **Address reliability** — retries, fallbacks, timeouts
5. **Address cost & latency** — caching, model selection, parallelism
6. **Address safety** — guardrails, permissions, audit logs

---

## Question 1: Design a Customer Support Agent

**Prompt**: Design an AI agent that handles customer support for an e-commerce platform.

### Solution Framework

```
User Message
    ↓
[Intent Classifier] — support, sales, escalate?
    ↓
[Context Builder]
  ├── Order history (database lookup)
  ├── Past tickets (episodic memory)
  └── Relevant policies (RAG)
    ↓
[Agent with Tools]
  ├── lookup_order(order_id)
  ├── check_return_eligibility(order_id)
  ├── initiate_refund(order_id) — requires confirmation
  ├── search_faqs(query)
  └── escalate_to_human(reason)
    ↓
[Output Guardrail]
  ├── Filter PII in response
  ├── Ensure response is in scope
  └── Block competitor mentions
    ↓
User Response + Action Taken
```

**Key Design Decisions**:
- Use Claude Haiku for intent classification (cheap), Sonnet for main agent
- Cache product policies in system prompt (prompt caching)
- `initiate_refund` requires human-in-the-loop confirmation
- Escalation path: after 3 failed resolution attempts → route to human
- Log all tool calls for audit (refund fraud prevention)
- SLA: < 5s response for 95th percentile

---

## Question 2: Design a Code Review Agent

**Prompt**: Design a multi-agent system that automatically reviews pull requests.

### Solution Framework

```
PR Webhook Event
    ↓
Orchestrator Agent
  → Parses diff, creates review plan
  → Spawns parallel specialist agents:

┌─────────────────────────────────────────────┐
│ [Security Agent]  [Style Agent]  [Logic Agent]│
│ - Injection vulns  - PEP8/lint   - Correctness│
│ - Hardcoded creds  - Naming      - Edge cases │
│ - OWASP top 10     - Comments    - Tests       │
└─────────────────────────────────────────────┘
    ↓ (parallel execution)
[Synthesizer Agent]
  → Deduplicates findings
  → Ranks by severity (critical/major/minor)
  → Formats as GitHub review comments
    ↓
GitHub API → Posts review
```

**Tools**:
- `read_file(path)` — access PR files
- `run_linter(code, language)` — static analysis
- `search_codebase(pattern)` — find similar code
- `post_review_comment(file, line, comment)` — GitHub API

**Scale considerations**:
- Fan out agents in parallel → 3× faster than sequential
- Use embeddings to detect duplicate findings across agents
- Rate limit GitHub API calls

---

## Question 3: Design a Research Agent

**Prompt**: Design an agent that researches a given topic and produces a comprehensive report.

### Solution Framework

```
Research Topic: "Impact of LLMs on software engineering"
    ↓
[Planner] — decomposes into sub-questions
  1. What are the productivity statistics?
  2. Which companies are adopting LLM coding tools?
  3. What are the risks and concerns?
  4. What do developers say?
    ↓
[Parallel Research Phase]
Each sub-question → Research Agent:
  ├── web_search(query)
  ├── arxiv_search(topic)
  ├── news_search(topic, date_range)
  └── summarize_page(url)
    ↓
[Fact Checker Agent]
  → Verifies key claims against sources
  → Flags contradictions
    ↓
[Writer Agent]
  → Synthesizes into structured report
  → Adds citations
  → Formats as Markdown
    ↓
[Editor Agent]
  → Reviews for coherence, coverage gaps
  → May trigger additional research loops
```

**Key challenges**:
- Context management: many search results → summarize before passing forward
- Citation tracking: map each claim to its source URL
- Avoiding bias: sample diverse sources
- Loop termination: max 3 research-write-review cycles

---

## Question 4: Design a Data Analysis Agent

**Prompt**: Design an agent that lets business users query their data in natural language.

### Solution Framework

```
User: "What were our top 5 products by revenue last quarter?"
    ↓
[Text-to-SQL Agent]
  → Understands schema (preloaded in context)
  → Generates SQL:
    SELECT product_name, SUM(revenue) as total
    FROM orders WHERE quarter = 'Q4-2024'
    GROUP BY product_name ORDER BY total DESC LIMIT 5
    ↓
[SQL Validator]
  → Parse and validate (no DROP/DELETE/INSERT)
  → Check query complexity (timeout risk)
  → Run with read-only DB user
    ↓
[Query Executor] — with 30s timeout
    ↓
[Result Interpreter Agent]
  → If < 10 rows: include raw data in context
  → If > 10 rows: summarize statistics
  → Generates natural language answer + chart spec
    ↓
User: "The top product was Widget A at $1.2M (32% of total revenue)"
    + Visualization
```

**Safety**:
- Read-only database role — no write permissions possible
- Query cost estimation before execution (EXPLAIN)
- Row limit (max 10,000 rows returned)
- Timeout at 30s with helpful error message

---

## Question 5: Design a Personal AI Assistant

**Prompt**: Design an AI assistant that integrates with email, calendar, and documents, has persistent memory, and can take actions on behalf of the user.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Personal Assistant                │
│                                                     │
│  Memory Layer:                                      │
│  ├── Short-term: current conversation               │
│  ├── Episodic: past conversations (vector DB)       │
│  └── Semantic: user preferences, facts              │
│                                                     │
│  Tools:                                             │
│  ├── read_email / send_email                        │
│  ├── create_event / check_calendar                  │
│  ├── read_document / create_document                │
│  ├── web_search                                     │
│  └── execute_task (delegates to sub-agent)          │
│                                                     │
│  Safety:                                            │
│  ├── Require confirmation for send_email            │
│  ├── OAuth scopes limit permissions                 │
│  └── Dry-run mode for calendar changes              │
└─────────────────────────────────────────────────────┘
```

**Key design considerations**:
- **Privacy**: email content never leaves user's infrastructure (local LLM or private API)
- **Memory consolidation**: nightly job extracts preferences from episodic memory
- **Proactive tasks**: background agent monitors for action items in email
- **Multi-device**: sync state via shared database

---

## Common Follow-Up Questions

**"How would you scale this to 1 million users?"**
- Horizontal scaling: stateless agent servers, shared state in Redis/Postgres
- Rate limiting per user to control costs
- Shared vector stores (multi-tenant with user_id filtering)
- CDN-cache static tool responses (e.g., company FAQs)
- Async processing for non-realtime tasks

**"How would you handle PII?"**
- Never log raw user messages — log anonymized task categories
- PII detection and redaction before logging tool results
- Data retention policies: delete conversation data after X days
- Encryption at rest and in transit for stored memories

**"What happens when the LLM API goes down?"**
- Circuit breaker → fast-fail instead of queue buildup
- Fallback to alternative LLM provider (OpenAI ↔ Anthropic)
- Graceful degradation: simple rule-based fallback for common queries
- Status page update + user notification
