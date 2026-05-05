# Agent Patterns — Interview Guide

## What is an AI Agent?

An AI agent is an LLM that can:
1. **Perceive** the environment (inputs, tool results, memory)
2. **Reason** about what to do next
3. **Act** via tools or output
4. **Observe** the result and repeat

The key distinction from a simple LLM call: **agents have a loop** — they can take multiple steps before producing a final answer.

## Core Agent Patterns

### 1. ReAct (Reason + Act)
The foundational pattern. Interleaves reasoning traces with actions.

```
[Thought] → [Action] → [Observation] → [Thought] → [Action] → ... → [Answer]
```

```python
while not done:
    thought = llm(prompt + history)
    if "Final Answer" in thought:
        return extract_answer(thought)
    action, action_input = parse_action(thought)
    observation = tools[action](action_input)
    history += f"\nObservation: {observation}"
```

**Pros**: simple, interpretable, widely supported  
**Cons**: can get stuck in reasoning loops, verbose

### 2. Plan-and-Execute
Separates planning from execution — a planner creates a task list, an executor runs each step.

```
User Query
    ↓
Planner LLM → [Step 1, Step 2, Step 3, ...]
    ↓
Executor → runs Step 1 → result
         → runs Step 2 using result → result
         → ...
    ↓
Synthesizer → final answer
```

**Pros**: better for long-horizon tasks, can re-plan on failure  
**Cons**: planner must anticipate future needs, re-planning adds latency

### 3. MRKL (Modular Reasoning, Knowledge and Language)
- Router LLM selects which "expert module" to call (calculator, search, SQL, etc.)
- Each module is a specialized tool or sub-model
- Predecessor to modern tool-use paradigm

### 4. Reflexion
- Agent executes a task
- Self-evaluates its output ("did I succeed?")
- Writes a reflection if failed
- Uses reflection as memory for next attempt
- Outperforms CoT on coding and reasoning benchmarks

```python
for attempt in range(max_attempts):
    result = agent.run(task)
    success = evaluator.check(result, task)
    if success:
        return result
    reflection = llm(f"You tried: {result}\nWhat went wrong and how to fix it?")
    memory.add(reflection)
```

### 5. Tree of Thoughts (ToT)
- Explore multiple reasoning paths simultaneously
- Prune bad paths, expand promising ones (BFS/DFS)
- Best for problems with clear intermediate evaluation (math proofs, code)
- Expensive: N branches × depth = many LLM calls

### 6. Self-Ask with Search
- Model identifies when it needs sub-questions
- Formulates "Follow up: ..." queries
- Answers each, then synthesizes
- Simple pattern; effective for multi-hop factual questions

### 7. LLM-as-Judge (Meta-Agent)
- A separate LLM evaluates the primary agent's output
- Scores for correctness, relevance, safety
- Can trigger re-generation if score below threshold
- Used in RLHF pipelines and production quality gates

## Agent Loop Design

### Termination Conditions (Critical for Safety)
```python
MAX_ITERATIONS = 10       # hard cap on steps
MAX_TOKENS = 50_000       # budget guard
TIMEOUT_SECONDS = 30      # wall clock limit

for i in range(MAX_ITERATIONS):
    response = agent_step(state)
    if response.is_final:
        return response.answer
    if tokens_used > MAX_TOKENS:
        return "Budget exceeded"
```
**Always have hard limits** — LLMs can loop indefinitely without them.

### State Management
```python
@dataclass
class AgentState:
    messages: list[Message]     # conversation history
    tool_calls: list[ToolCall]  # what was executed
    observations: list[str]     # tool results
    scratchpad: str             # working memory
    iterations: int             # loop counter
```

## Agentic System Levels (Anthropic's Model)
1. **Single-turn**: one LLM call, no loop
2. **Multi-turn**: conversation, user drives next step
3. **Tool-augmented**: LLM calls tools, returns result
4. **Agentic**: autonomous loop with multiple tool calls
5. **Multi-agent**: multiple LLMs collaborating

## Common Interview Questions

**Q: What's the difference between a chain and an agent?**
A: A chain has a fixed, predetermined sequence of steps (hardcoded by the developer). An agent dynamically decides at each step which tool to call and when to stop — the path is determined by the LLM at runtime.

**Q: How do you prevent an agent from looping infinitely?**
A: (1) Max iteration count, (2) token budget limit, (3) timeout, (4) detect repeated tool calls (cycle detection), (5) require explicit "Final Answer" format to terminate.

**Q: When would you use Plan-and-Execute over ReAct?**
A: Plan-and-Execute for long-horizon tasks (5+ steps) where you want the agent to think ahead. ReAct for shorter tasks or when you need to adapt dynamically based on each observation. Plan-and-Execute is better for parallelizable sub-tasks.

**Q: What is the Cognitive Architecture of an agent?**
A: Cognitive architecture refers to how memory, planning, action, and perception are organized. Components: working memory (context window), long-term memory (vector store), planner, executor, and perception (tool results, user input).
