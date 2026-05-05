# LangChain & LangGraph — Interview Guide

## LangChain Core Concepts

LangChain provides abstractions over LLMs, prompts, chains, and tools.

### Key Abstractions
| Abstraction | What it is |
|---|---|
| `ChatModel` | Wrapper around any LLM API |
| `PromptTemplate` | Reusable, parameterized prompts |
| `Chain` | Sequence of LLM calls / transformations |
| `Tool` | Function the agent can call |
| `VectorStore` | Abstraction over vector databases |
| `Memory` | Conversation history management |
| `Agent` | LLM + tools + loop |

### Basic Agent (LangChain)
```python
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate

@tool
def search_web(query: str) -> str:
    """Search the web for current information."""
    return f"Search results for: {query}"

llm = ChatAnthropic(model="claude-sonnet-4-6")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with web search."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, [search_web], prompt)
executor = AgentExecutor(agent=agent, tools=[search_web], verbose=True)
result = executor.invoke({"input": "What is the latest news about AI?"})
```

## LangGraph — Graph-Based Agents

LangGraph models agent workflows as **state machines** (directed graphs). Each node is a function; edges define transitions.

### Why LangGraph over LangChain agents?
- **Full control** over the loop — no hidden logic
- **Conditional branching** based on agent state
- **Cycles** for ReAct loops
- **Persistence** — save/resume mid-execution
- **Streaming** at each node
- **Human-in-the-loop** — pause for approval

### Core Concepts
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # append-only list
    next_step: str
    iterations: int
```

### Simple ReAct Agent in LangGraph
```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Define nodes
def call_llm(state: AgentState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

tool_node = ToolNode(tools=[search_web, calculator])

# Build graph
graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("tools", tool_node)

graph.set_entry_point("llm")
graph.add_conditional_edges("llm", should_continue)
graph.add_edge("tools", "llm")

app = graph.compile()

# Run
result = app.invoke({"messages": [HumanMessage("What is 15% of $89.50?")]})
```

### Human-in-the-Loop
```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["tools"]  # pause before any tool execution
)

config = {"configurable": {"thread_id": "session-123"}}

# Run until interrupt
result = app.invoke({"messages": [HumanMessage("Delete all test files")]}, config)

# Show pending action to human
print("Agent wants to run:", result["messages"][-1].tool_calls)

# Resume after approval
if user_approves():
    final = app.invoke(None, config)  # None = resume from checkpoint
```

### Persistence and Checkpointing
```python
from langgraph.checkpoint.postgres import PostgresSaver

# Persist state to Postgres — survives crashes
checkpointer = PostgresSaver.from_conn_string("postgresql://localhost/agents")
app = graph.compile(checkpointer=checkpointer)

# Resume a specific thread
config = {"configurable": {"thread_id": "user-abc-session-1"}}
state = app.get_state(config)  # view current state
```

### Subgraphs (Multi-Agent in LangGraph)
```python
# Each agent is its own compiled graph
researcher = researcher_graph.compile()
writer = writer_graph.compile()

# Orchestrator calls them as nodes
def run_researcher(state):
    return researcher.invoke(state)

orchestrator = StateGraph(OrchestratorState)
orchestrator.add_node("research", run_researcher)
orchestrator.add_node("write", run_writer)
```

## LangGraph vs LangChain Agents

| Feature | LangChain AgentExecutor | LangGraph |
|---|---|---|
| Control flow | Hidden in AgentExecutor | Fully explicit graph |
| Branching | Limited | Full conditional logic |
| Cycles | Yes (ReAct loop) | Yes + more control |
| Human-in-loop | Hacky | First-class feature |
| Persistence | Limited | Built-in checkpointing |
| Debugging | Callbacks | Full state inspection |
| Multi-agent | Manual | Subgraph pattern |

## Common Interview Questions

**Q: Why use LangGraph instead of a simple while loop?**
A: LangGraph adds: (1) built-in checkpointing/persistence, (2) human-in-the-loop interrupts, (3) streaming node-by-node, (4) time-travel debugging (replay from any checkpoint), (5) parallel branch execution. For simple agents, a while loop is fine. For production systems, LangGraph's infrastructure wins.

**Q: How does LangGraph handle errors in the middle of a workflow?**
A: With checkpointing enabled, the state is saved before each node. On error, you can replay from the last checkpoint with a fix. Without checkpointing, you must restart from the beginning. Checkpointing is essential for long-running or expensive agent workflows.

**Q: What is the difference between a node and an edge in LangGraph?**
A: Nodes are functions that transform state (call LLM, execute tool, process result). Edges define which node runs next — either fixed (`add_edge`) or conditional (`add_conditional_edges` with a routing function). The graph executes by following edges from one node to the next until it reaches END.
