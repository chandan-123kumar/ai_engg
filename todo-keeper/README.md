# todo-keeper

A Claude Code plugin for **local-first personal TODOs** that surface at the right moment during your sessions — at most once every 6 hours, never as a noisy popup.

- **Local-only.** State lives in `~/.claude-todo-keeper/state.json`. No cloud, no accounts, no telemetry.
- **Tasteful surfacing.** A `SessionStart` hook injects pending TODOs as session context with instructions for Claude to mention them only at natural breaks.
- **Two ways to use.** Slash command (`/todo add ...`) for explicit control, or just talk to Claude (*"remind me to ship the PR"*).

## Install (one liner)

Inside any Claude Code session:

```
/plugin marketplace add chandan-ku/todo-keeper && /plugin install todo-keeper@todo-keeper
```

Restart the session (or open a new one) so the `SessionStart` hook registers.

> Replace `chandan-ku/todo-keeper` with `<your-gh-user>/<repo>` if you forked it.

## Usage

### Slash command

```
/todo add "review PR #42"
/todo add "reply to Anu's email"
/todo list
/todo list --all          # include completed
/todo done a1b2
/todo rm a1b2
```

### Natural language

> *"Remind me to update the README screenshots."*
> *"What's on my todo list?"*
> *"I finished the websocket fix — mark it done."*

The bundled `todo-keeper` skill picks these up and calls the CLI for you.

### Surfacing

The first session you open after a 6-hour gap, Claude sees your pending TODOs as additional context with instructions to surface them when it makes sense — not at the very start, and not when you're mid-focus on something unrelated. Rate-limited so it never becomes nagging.

## How it works

```
todo-keeper/
├── .claude-plugin/
│   ├── plugin.json           # registers commands, skills, SessionStart hook
│   └── marketplace.json      # makes it installable via /plugin install
├── commands/
│   └── todo.md               # /todo slash command
├── skills/
│   └── todo-keeper/
│       └── SKILL.md          # natural-language entry point
├── hooks/
│   ├── todo_cli.py           # all CRUD logic + `surface` command
│   └── session_start.sh      # runs `todo_cli.py surface` on each session
└── README.md
```

State file schema (`~/.claude-todo-keeper/state.json`):

```json
{
  "todos": [
    {
      "id": "a1b2",
      "text": "review PR #42",
      "created": "2026-06-28T09:00:00+00:00",
      "done": false
    }
  ],
  "last_surfaced_at": "2026-06-28T07:00:00+00:00"
}
```

The surfacing rate limit is enforced by `cmd_surface` in `todo_cli.py` — if `now - last_surfaced_at < 6h` or there are no pending TODOs, the hook prints nothing and the session starts clean.

## Manual install (without the marketplace)

```bash
git clone https://github.com/chandan-ku/todo-keeper.git ~/.claude/plugins/todo-keeper
# Then enable in ~/.claude/settings.json:
#   "plugins": { "todo-keeper": { "enabled": true } }
```

## Try the CLI standalone

The CLI works on its own — no Claude needed:

```bash
python3 hooks/todo_cli.py add "test todo"
python3 hooks/todo_cli.py list
python3 hooks/todo_cli.py surface     # prints injection block if >6h since last
```

## Uninstall

```
/plugin uninstall todo-keeper@todo-keeper
rm -rf ~/.claude-todo-keeper
```

## License

MIT — see `LICENSE`.
