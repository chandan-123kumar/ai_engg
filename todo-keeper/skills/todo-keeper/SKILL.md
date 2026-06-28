---
name: todo-keeper
description: Use when the user says "remind me to X", "add a todo", "I need to remember X", "what's on my todo list", "mark X as done", or otherwise wants to manage personal TODOs that persist across Claude Code sessions. Stores TODOs locally and surfaces pending ones at session start (rate-limited to once per 6 hours).
---

# todo-keeper

A local-first personal TODO list. The user's TODOs live at `~/.claude-todo-keeper/state.json` and are managed via the bundled CLI at `${CLAUDE_PLUGIN_ROOT}/hooks/todo_cli.py`.

## When to invoke

Triggers — natural-language phrases that should call this skill:

- "remind me to X" / "remember to X" / "don't let me forget X"
- "add a todo" / "add this to my list" / "save that as a todo"
- "what's on my todo list" / "show my todos" / "what do I have pending"
- "I finished X" / "mark X done" / "X is done"
- "drop X from my list" / "remove X"

Do NOT invoke for in-conversation task tracking (use the TaskCreate tool for that). This skill is for the user's *personal* persistent TODOs across sessions.

## How to use

The CLI takes these subcommands. Always invoke it via the absolute path so it works regardless of cwd:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/todo_cli.py add "<text>"
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/todo_cli.py list
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/todo_cli.py list --all
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/todo_cli.py done <id>
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/todo_cli.py rm <id>
```

When the user wants to mark something done but only gives a description (not an id), first run `list`, find the matching todo by text, then call `done` with its id. If multiple match, ask which one.

## Surfacing behavior

A `SessionStart` hook injects pending TODOs into the session context at most once every 6 hours. When you see a `<todo-keeper-reminder>` block in the system context, follow its guidance: mention pending items only at a natural break in the conversation, never as the opening line of a session.

## Output style

After running the CLI, repeat the CLI's stdout to the user verbatim — it's already terse and human-readable. Add at most one short sentence of acknowledgement ("Added." / "Done.").
