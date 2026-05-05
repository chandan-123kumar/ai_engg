# Conceptual Interview Questions — Agentic AI

## Foundational Concepts

**Q: What is the difference between an LLM and an AI agent?**

An LLM is a stateless function: it takes tokens in and produces tokens out. An AI agent is a system that wraps an LLM in a loop: it can observe its environment, take actions via tools, receive observations, and decide whether to act again or return a final answer. The agent has **memory**, **goals**, and **autonomy** over multiple steps — the LLM is just the reasoning engine inside it.

---

**Q: Explain the ReAct pattern. Why is it effective?**

ReAct (Reasoning + Acting) interleaves thought traces with tool calls:
```
Thought: I need to find X
Action: search("X")
Observation: [result]
Thought: Now I can answer
Answer: [final answer]
```
Effective because: (1) reasoning traces reduce hallucination by making the model "work out loud", (2) observations ground subsequent reasoning in real data, (3) it's interpretable — you can see exactly why the agent did what it did.

---

**Q: What is grounding and why do agents need it?**

Grounding connects the LLM's outputs to verified, real-world information. Without grounding, LLMs confabulate — generating plausible-sounding but false information. Agents ground themselves through:
- **Tool use**: search results, database queries, API calls
- **RAG**: retrieved documents with citations
- **Structured outputs**: constrained to valid options only

---

**Q: What's the difference between RAG and fine-tuning for knowledge?**

| | RAG | Fine-tuning |
|---|---|---|
| Knowledge freshness | Real-time (just update docs) | Static (baked in at training) |
| Citability | Yes (source documents) | No |
| Cost | Retrieval at inference time | Training cost upfront |
| Failure mode | Retrieval misses → wrong answer | Hallucination on edge cases |
| Best for | Dynamic/private knowledge | Style, format, reasoning patterns |

Use RAG for facts. Use fine-tuning for how the model should reason and respond.

---

**Q: How does context length affect agentic systems?**

- **Positive**: longer context allows more history, larger retrieved chunks, more tool results
- **Negative**: cost scales linearly with context; attention quality degrades at long contexts ("lost in the middle"); inference latency increases
- **Agent implication**: don't naively concatenate all history — compress, summarize, or use external memory to keep context relevant and affordable

---

**Q: What is "agentic loop" and what are its risks?**

The agentic loop: LLM reasons → calls tool → receives result → reasons again. Risks:
1. **Infinite loops**: agent can't find answer, keeps searching forever → hard token/iteration limits
2. **Compounding errors**: wrong tool call → bad observation → wrong next action → worse outcome
3. **Cost explosion**: each loop iteration costs money; uncapped loops can be expensive
4. **Hallucinated tool calls**: agent fabricates tool results instead of actually calling tools

---

## Architecture Questions

**Q: When would you choose a single-agent vs multi-agent approach?**

Single agent for:
- Simple to medium complexity tasks (< 5 tools, short context)
- When latency is critical (fewer LLM calls)
- When debugging simplicity matters

Multi-agent for:
- Tasks that benefit from parallelism (independent sub-tasks)
- When specialization improves quality (code agent vs. search agent vs. writer agent)
- Very long tasks that exceed a single context window
- When you want peer review (critic/debate pattern)

Rule: start with single agent, add complexity only when you hit a bottleneck.

---

**Q: How do you handle tool errors in an agent?**

1. **Don't raise exceptions** — return structured error messages to the LLM
2. **Include actionable information**: "File not found at /tmp/output.csv. Try checking /data/ directory."
3. **Let the LLM decide**: it may retry with different params, use a fallback tool, or inform the user
4. **Log the error** for debugging
5. **Hard limits**: after 3 failures of the same tool, return an error to the user — don't let the agent loop indefinitely on a broken tool

---

**Q: How does planning differ from reasoning in agents?**

- **Reasoning**: step-by-step thinking within a single LLM call (CoT, ReAct)
- **Planning**: generating a sequence of future steps before executing any of them (Plan-and-Execute pattern)

Planning is better for long-horizon tasks because it lets the agent anticipate dependencies. Reasoning is more adaptive — it responds to each observation before deciding the next step. Many production systems combine both: high-level plan + adaptive ReAct execution.

---

**Q: What is the role of the system prompt in an agent?**

The system prompt defines the agent's:
- **Persona**: who it is, what it knows, how it talks
- **Capabilities**: what tools it has and when to use them
- **Constraints**: what it must NOT do (scope, safety, format)
- **Output format**: how to structure responses (JSON schema, sections)

The system prompt is the most important piece of engineering for agent quality. It's also the most cacheable (prompt caching), making it cost-effective to put significant content there.

---

## Advanced Questions

**Q: What is prompt injection and why is it especially dangerous for agents?**

Prompt injection: malicious content in the agent's environment that hijacks its behavior. For a simple chatbot, the worst case is a bad response. For an agent with tools:
- A malicious web page could instruct the agent to send emails, delete files, or exfiltrate data
- The agent has the authority to take real-world actions
- The user trusts the agent to act on their behalf

Defense: least-privilege tools, input sanitization, confirmation for irreversible actions, privilege separation between trusted and untrusted content.

---

**Q: Explain the "alignment tax" in agentic systems.**

The alignment tax refers to the performance cost of making an agent safe and reliable:
- Safety guardrails add latency (extra LLM calls for validation)
- Confirmation dialogs add friction for users
- Constrained outputs (refusing edge cases) reduce task completion rate
- Logging and audit trails add infrastructure cost

The engineering challenge: minimize the alignment tax while maintaining acceptable safety. Techniques: fast lightweight guardrail models (Haiku), async safety checks, smart confirmation triggers (only for high-risk actions).

---

**Q: How would you build an agent that improves over time?**

1. **Collect data**: log all agent runs with success/failure labels
2. **Identify failure patterns**: cluster failures by type (wrong tool, bad retrieval, logic error)
3. **Improve prompts**: update system prompt with few-shot examples for failure cases
4. **Improve tools**: fix tools that return confusing results
5. **Improve retrieval**: tune chunking/embedding if RAG misses
6. **Fine-tune (if justified)**: SFT on successful trajectories
7. **Eval regression**: run full eval suite after each change to catch regressions

Key insight: most improvement comes from better prompts and better tools, not bigger models.

---

**Q: What's your mental model for deciding when to use an agent vs. a simpler approach?**

Use the simplest thing that works:
- **Single LLM call** if the task is one step and doesn't need external info
- **Retrieval + LLM** if you need up-to-date or private knowledge
- **Tool-augmented LLM** if you need one or two external actions
- **Agent loop** if the task requires multiple steps whose sequence isn't known in advance
- **Multi-agent** if sub-tasks are independent and parallelizable or require specialization

Agents introduce complexity, cost, and latency. Don't use them unless you need the autonomy.
