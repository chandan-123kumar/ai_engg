---
description: Manage local TODOs (add, list, done, rm). Stored at ~/.claude-todo-keeper/state.json.
argument-hint: <add "text" | list [--all] | done <id> | rm <id>>
---

Run the todo-keeper CLI with the user's arguments and report the result.

Execute exactly:

```
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/todo_cli.py $ARGUMENTS
```

Then:
- Print the command's stdout to the user verbatim.
- If exit code is non-zero, briefly explain what went wrong and show the usage hint.
- Do not invent extra commands beyond: add, list (--all), done <id>, rm <id>.
- For `add`, the text after `add` is the todo content — quote it if it contains spaces.

Examples the user might type:
- `/todo add "review PR #42"`
- `/todo list`
- `/todo list --all`
- `/todo done a1b2`
- `/todo rm a1b2`
