# Agentic AI Engineering — Interview Roadmap

A structured, interview-focused roadmap for Agentic AI Engineers. Each section maps to real interview domains.

## Structure

```
agentic_ai_engg/
├── 01_foundations/
│   ├── llm_fundamentals.md         — Transformers, attention, inference
│   ├── prompt_engineering.md       — CoT, few-shot, structured output
│   └── rag_fundamentals.md         — Retrieval, chunking, reranking
├── 02_agent_architecture/
│   ├── agent_patterns.md           — ReAct, Plan-and-Execute, MRKL
│   ├── tool_use.md                 — Function calling, tool design
│   ├── memory_systems.md           — Short/long-term, episodic, semantic
│   └── multi_agent_systems.md      — Orchestration, communication, roles
├── 03_frameworks/
│   ├── langchain_langgraph.md      — Graph-based agent orchestration
│   ├── autogen.md                  — Microsoft multi-agent framework
│   ├── crewai.md                   — Role-based crew orchestration
│   └── anthropic_sdk.md            — Claude API, tool use, caching
├── 04_evaluation_and_safety/
│   ├── agent_evaluation.md         — Benchmarks, metrics, evals
│   ├── guardrails.md               — Input/output validation, safety
│   └── observability.md            — Tracing, logging, LangSmith
├── 05_production/
│   ├── latency_and_cost.md         — Optimization, caching, batching
│   ├── reliability.md              — Retries, fallbacks, circuit breakers
│   └── deployment.md               — Serving, scaling, APIs
├── 06_interview_questions/
│   ├── conceptual_qs.md            — Theory and design questions
│   ├── system_design_qs.md         — Agent system design prompts
│   └── coding_qs.md                — Hands-on coding challenges
└── 07_projects/
    ├── project_ideas.md            — Portfolio projects for interviews
    └── case_studies.md             — Real-world agent architectures
```

## Interview Domains by Company Type

| Company Type | Top Focus Areas |
|---|---|
| AI Startups | Agent loops, tool use, LangGraph, speed |
| Big Tech (AI teams) | Scalability, evals, safety, system design |
| Enterprise SaaS | RAG pipelines, cost optimization, reliability |
| Research Labs | Architecture depth, novel approaches, benchmarks |

## Study Order

1. [LLM Fundamentals](01_foundations/llm_fundamentals.md) — must-know baseline
2. [Prompt Engineering](01_foundations/prompt_engineering.md) — every interview tests this
3. [Agent Patterns](02_agent_architecture/agent_patterns.md) — core agentic concepts
4. [Tool Use](02_agent_architecture/tool_use.md) — most common hands-on question
5. [Multi-Agent Systems](02_agent_architecture/multi_agent_systems.md) — senior-level design
6. [Evaluation & Safety](04_evaluation_and_safety/agent_evaluation.md) — differentiator
7. [Production](05_production/latency_and_cost.md) — shows real-world maturity
8. [Interview Questions](06_interview_questions/system_design_qs.md) — practice
