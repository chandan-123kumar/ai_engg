# AutoGen — Interview Guide

## What is AutoGen?

Microsoft's open-source framework for building multi-agent conversational systems. Agents talk to each other via a message-passing interface. Best for: debate/critic patterns, code generation with execution, automated workflows.

## Core Concepts

### ConversableAgent
Every agent in AutoGen is a `ConversableAgent` — it can send and receive messages.

```python
import autogen

config_list = [{"model": "claude-sonnet-4-6", "api_key": "...", "api_type": "anthropic"}]

assistant = autogen.AssistantAgent(
    name="Assistant",
    llm_config={"config_list": config_list},
    system_message="You are a helpful AI assistant."
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",  # NEVER | ALWAYS | TERMINATE
    max_consecutive_auto_reply=10,
    code_execution_config={"work_dir": "coding"},
)
```

### Two-Agent Conversation
```python
user_proxy.initiate_chat(
    assistant,
    message="Write a Python function to calculate fibonacci numbers and test it."
)
```

AutoGen will:
1. User sends task to Assistant
2. Assistant generates code
3. User proxy executes code, returns result
4. Assistant fixes if tests fail
5. Terminates when code passes or max_replies reached

### GroupChat (Multi-Agent)
```python
researcher = autogen.AssistantAgent("Researcher", llm_config=config, 
    system_message="You research topics on the web.")
writer = autogen.AssistantAgent("Writer", llm_config=config,
    system_message="You write clear summaries from research.")
critic = autogen.AssistantAgent("Critic", llm_config=config,
    system_message="You critique and improve written content.")

groupchat = autogen.GroupChat(
    agents=[researcher, writer, critic, user_proxy],
    messages=[],
    max_round=12,
    speaker_selection_method="auto"  # LLM decides who speaks next
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=config)
user_proxy.initiate_chat(manager, message="Write a report on LLM trends in 2025.")
```

## AutoGen vs LangGraph

| Feature | AutoGen | LangGraph |
|---|---|---|
| Paradigm | Agents talk to each other | State machine with nodes |
| Control flow | Emergent (LLM decides) | Explicit (developer defines) |
| Code execution | Built-in executor | Manual tool |
| Best for | Conversational multi-agent | Production workflows |
| Debugging | Harder (emergent flow) | Easier (explicit graph) |

## Common Interview Questions

**Q: When would you choose AutoGen over LangGraph?**
A: AutoGen for quick multi-agent prototyping, especially when you want agents to converse naturally and code execution is central. LangGraph for production systems where you need explicit control flow, checkpointing, human-in-the-loop, and predictable execution paths.
