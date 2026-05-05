# CrewAI — Interview Guide

## What is CrewAI?

Role-based multi-agent framework. You define agents by role/goal/backstory, assign tasks, and a "crew" executes them. More opinionated than LangGraph but faster to prototype.

## Core Concepts

```python
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

search_tool = SerperDevTool()

# Define agents by role
researcher = Agent(
    role="Senior Research Analyst",
    goal="Uncover cutting-edge developments in AI and data science",
    backstory="You are an expert at finding and synthesizing research papers.",
    tools=[search_tool],
    verbose=True,
    llm="claude-sonnet-4-6"
)

writer = Agent(
    role="Tech Content Strategist",
    goal="Craft compelling content on tech advancements",
    backstory="You transform complex technical concepts into engaging narratives.",
    verbose=True,
    llm="claude-sonnet-4-6"
)

# Define tasks
research_task = Task(
    description="Research the latest developments in agentic AI systems.",
    expected_output="A list of 10 key findings with sources.",
    agent=researcher
)

write_task = Task(
    description="Write a blog post based on the research findings.",
    expected_output="A 500-word blog post in Markdown format.",
    agent=writer,
    context=[research_task]  # depends on research_task output
)

# Assemble crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,  # or Process.hierarchical
    verbose=True
)

result = crew.kickoff()
```

## Process Types

| Process | How | Best for |
|---|---|---|
| Sequential | Tasks run one after another | Linear pipelines |
| Hierarchical | Manager agent delegates to workers | Complex coordination |
| Parallel | Tasks run simultaneously | Independent research tasks |

## CrewAI vs LangGraph vs AutoGen

| | CrewAI | LangGraph | AutoGen |
|---|---|---|---|
| Learning curve | Low | Medium | Medium |
| Control | Low (opinionated) | High (explicit) | Medium |
| Production-ready | Medium | High | Medium |
| Role abstraction | First-class | Manual | Manual |

## Common Interview Questions

**Q: Why is CrewAI useful for rapid prototyping?**
A: The role/goal/backstory abstraction makes it fast to spin up specialized agents without building state machines. The `context` dependency between tasks handles handoffs automatically. For production, you'd likely migrate to LangGraph for more control.

**Q: What's the limitation of the hierarchical process in CrewAI?**
A: The manager agent uses LLM to coordinate — it can make poor routing decisions, and you can't explicitly control which agent handles which subtask. LangGraph's conditional edges give you explicit control that production systems need.
