# Agent Evaluation — Interview Guide

## Why Evaluation is Hard for Agents

Unlike classification (accuracy against labels), agents produce:
- Open-ended text (no single correct answer)
- Multi-step trajectories (the path matters, not just the end)
- Non-deterministic outputs (temperature > 0)
- Side effects (tool calls, actions taken)

Evaluation must cover: **correctness, efficiency, safety, and robustness**.

## Evaluation Dimensions

### 1. Task Success Rate
Did the agent complete the task?

```python
def evaluate_task_success(task: str, agent_output: str, expected: str) -> float:
    # LLM-as-judge for open-ended tasks
    prompt = f"""
    Task: {task}
    Expected outcome: {expected}
    Agent output: {agent_output}
    
    Did the agent successfully complete the task? Score 0-1.
    Return JSON: {{"score": 0.8, "reason": "..."}}
    """
    result = judge_llm.invoke(prompt)
    return json.loads(result)["score"]
```

### 2. Trajectory / Step Quality
Did the agent take the right steps?

```python
def evaluate_trajectory(
    task: str,
    steps: list[AgentStep],
    ideal_steps: list[str]
) -> dict:
    return {
        "efficiency": len(ideal_steps) / len(steps),     # 1.0 = no wasted steps
        "correct_tools_used": check_tools(steps, ideal_steps),
        "unnecessary_calls": count_redundant_steps(steps),
        "hallucinated_tool_calls": count_invalid_calls(steps)
    }
```

### 3. Faithfulness (for RAG agents)
Is the answer supported by retrieved context?

```python
# RAGAS faithfulness
# For each claim in answer, check if it's in context
claims = extract_claims(answer)
supported = [c for c in claims if is_supported_by_context(c, context)]
faithfulness = len(supported) / len(claims)
```

### 4. Tool Call Accuracy
Did the agent call the right tools with the right inputs?

```python
@dataclass
class ToolCallEval:
    tool_name_correct: bool
    input_schema_valid: bool
    input_semantically_correct: bool
    unnecessary_call: bool

def eval_tool_call(actual: ToolCall, expected: ToolCall) -> ToolCallEval:
    return ToolCallEval(
        tool_name_correct=actual.name == expected.name,
        input_schema_valid=validate_schema(actual.input, actual.name),
        input_semantically_correct=semantic_match(actual.input, expected.input),
        unnecessary_call=actual not in expected_calls
    )
```

## Evaluation Frameworks

### RAGAS (RAG Assessment)
```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,          # answer grounded in context?
    answer_relevancy,      # answer relevant to question?
    context_precision,     # retrieved context accurate?
    context_recall         # all needed info retrieved?
)

result = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)
```

### AgentBench / τ-bench
Open-source benchmarks for agent tasks:
- **AgentBench**: DB, OS, KG, web tasks
- **τ-bench**: retail and airline customer service tasks
- **SWE-bench**: real GitHub issues (code agents)
- **GAIA**: real-world assistant tasks

### LLM-as-Judge Pattern
```python
JUDGE_PROMPT = """
You are evaluating an AI agent's response.

Task: {task}
Agent Response: {response}

Score on these dimensions (0-1 each):
1. Correctness: Is the answer factually correct?
2. Completeness: Does it fully address the task?
3. Conciseness: Is it appropriately concise?
4. Safety: Does it avoid harmful content?

Return JSON: {{"correctness": 0.9, "completeness": 0.8, "conciseness": 0.7, "safety": 1.0, "reasoning": "..."}}
"""

def judge(task, response):
    result = judge_llm.invoke(JUDGE_PROMPT.format(task=task, response=response))
    return json.loads(result)
```

**LLM-as-judge pitfalls**:
- **Position bias**: prefers first answer in A/B comparisons
- **Verbosity bias**: prefers longer, detailed answers
- **Self-enhancement**: a model judges itself favorably
- **Mitigation**: calibration examples, multiple judges, diverse judge models

## Evaluation Dataset Construction

### Sources
1. **Golden set**: human-curated task + expected output pairs
2. **Production logs**: real user queries (anonymized)
3. **Synthetic**: LLM-generated with human review
4. **Adversarial**: edge cases, prompt injections, jailbreaks

### Stratification
```python
eval_set = {
    "easy": 30%,    # single-step, clear answer
    "medium": 50%,  # 2-4 steps, some ambiguity
    "hard": 20%,    # multi-hop, edge cases
}
```

## Regression Testing for Agents

```python
# Run eval suite on every code change
def regression_eval():
    results = []
    for test_case in eval_suite:
        output = agent.run(test_case.query)
        score = evaluate(test_case, output)
        results.append(score)
    
    avg_score = mean(results)
    if avg_score < BASELINE_SCORE - TOLERANCE:
        raise RegressionError(f"Score {avg_score} below baseline {BASELINE_SCORE}")
```

## Common Interview Questions

**Q: How do you evaluate an agent that takes irreversible actions?**
A: Use simulation — build a mock environment where tool calls are logged but not executed. Evaluate against expected tool call sequences. For production, use shadow mode: run the agent in parallel with humans, compare decisions (don't execute agent's actions).

**Q: What's the hardest metric to measure for agents?**
A: Trajectory efficiency. An agent that gets the right answer in 10 steps vs 3 steps is functionally equivalent to the user but very different in cost and latency. Measuring "optimal" steps requires ground truth of the ideal path, which is expensive to create.

**Q: How do you build a regression test suite for agents?**
A: (1) Log all production interactions, (2) select diverse, representative subset, (3) have humans label expected outcomes, (4) run suite on every deploy, (5) alert if success rate drops > X%. Automate with CI/CD integration.

**Q: What's the difference between offline and online evaluation?**
A: Offline: run agent against static eval set, compare to golden answers — fast, cheap, deterministic. Online: A/B test in production, measure real user satisfaction (thumbs up/down, task completion, churn) — ground truth but slow, expensive, affects users.
