#!/usr/bin/env python3
"""todo-keeper CLI — local-first TODO storage.

State file: ~/.claude-todo-keeper/state.json
Schema:
{
  "todos": [{"id": str, "text": str, "created": iso8601, "done": bool}],
  "last_surfaced_at": iso8601 | null
}

Commands:
  add "<text>"     Add a new todo. Prints the id.
  list             Print pending todos.
  list --all       Include completed.
  done <id>        Mark a todo done (prefix match on id).
  rm <id>          Delete a todo (prefix match on id).
  pending          Print only pending count (for hook use).
  surface          Print pending todos formatted for hook injection,
                   honoring 6h rate limit. Updates last_surfaced_at.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

STATE_DIR = Path(os.path.expanduser("~/.claude-todo-keeper"))
STATE_FILE = STATE_DIR / "state.json"
SURFACE_INTERVAL = timedelta(hours=6)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load() -> dict:
    if not STATE_FILE.exists():
        return {"todos": [], "last_surfaced_at": None}
    try:
        return json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        backup = STATE_FILE.with_suffix(".corrupt.json")
        STATE_FILE.rename(backup)
        return {"todos": [], "last_surfaced_at": None}


def _save(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


def _human_age(iso: str) -> str:
    try:
        created = datetime.fromisoformat(iso)
    except ValueError:
        return "?"
    delta = datetime.now(timezone.utc) - created
    s = int(delta.total_seconds())
    if s < 60:
        return "just now"
    if s < 3600:
        return f"{s // 60}m ago"
    if s < 86400:
        return f"{s // 3600}h ago"
    return f"{s // 86400}d ago"


def _find(state: dict, prefix: str):
    matches = [t for t in state["todos"] if t["id"].startswith(prefix)]
    if not matches:
        return None, f"no todo matches id prefix '{prefix}'"
    if len(matches) > 1:
        ids = ", ".join(t["id"] for t in matches)
        return None, f"ambiguous prefix '{prefix}': matches {ids}"
    return matches[0], None


def cmd_add(args: list[str]) -> int:
    if not args:
        print("usage: todo add \"<text>\"", file=sys.stderr)
        return 2
    text = " ".join(args).strip()
    if not text:
        print("error: empty todo", file=sys.stderr)
        return 2
    state = _load()
    new = {
        "id": secrets.token_hex(2),
        "text": text,
        "created": _now(),
        "done": False,
    }
    state["todos"].append(new)
    _save(state)
    print(f"added [{new['id']}] {text}")
    return 0


def cmd_list(args: list[str]) -> int:
    show_all = "--all" in args
    state = _load()
    items = state["todos"] if show_all else [t for t in state["todos"] if not t["done"]]
    if not items:
        print("(no todos)" if show_all else "(no pending todos)")
        return 0
    for t in items:
        mark = "x" if t["done"] else " "
        print(f"[{mark}] {t['id']}  {t['text']}  ({_human_age(t['created'])})")
    return 0


def cmd_done(args: list[str]) -> int:
    if not args:
        print("usage: todo done <id>", file=sys.stderr)
        return 2
    state = _load()
    todo, err = _find(state, args[0])
    if err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    todo["done"] = True
    _save(state)
    print(f"done [{todo['id']}] {todo['text']}")
    return 0


def cmd_rm(args: list[str]) -> int:
    if not args:
        print("usage: todo rm <id>", file=sys.stderr)
        return 2
    state = _load()
    todo, err = _find(state, args[0])
    if err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    state["todos"] = [t for t in state["todos"] if t["id"] != todo["id"]]
    _save(state)
    print(f"removed [{todo['id']}] {todo['text']}")
    return 0


def cmd_pending(_args: list[str]) -> int:
    state = _load()
    print(sum(1 for t in state["todos"] if not t["done"]))
    return 0


def cmd_surface(_args: list[str]) -> int:
    """Print pending todos formatted for SessionStart context injection.

    Honors the 6h rate limit. Silent (exit 0, no output) if:
      - no pending todos
      - last surfaced within SURFACE_INTERVAL
    Updates last_surfaced_at on successful surface.
    """
    state = _load()
    pending = [t for t in state["todos"] if not t["done"]]
    if not pending:
        return 0

    last = state.get("last_surfaced_at")
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            if datetime.now(timezone.utc) - last_dt < SURFACE_INTERVAL:
                return 0
        except ValueError:
            pass

    lines = ["<todo-keeper-reminder>"]
    lines.append(
        f"The user has {len(pending)} pending personal TODO"
        f"{'s' if len(pending) != 1 else ''} stored locally:"
    )
    for t in pending:
        lines.append(f"  - [{t['id']}] {t['text']} (added {_human_age(t['created'])})")
    lines.append("")
    lines.append(
        "If a natural moment arises in this session (a task completes, the user "
        "pauses, or work wraps up), gently mention one or more of these in a single "
        "short sentence. Do NOT dump the list unsolicited at the start of the session. "
        "Do NOT mention them if the user is mid-task on something unrelated and "
        "focused. The user can run `/todo done <id>` to mark items complete."
    )
    lines.append("</todo-keeper-reminder>")
    print("\n".join(lines))

    state["last_surfaced_at"] = _now()
    _save(state)
    return 0


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "ls": cmd_list,
    "done": cmd_done,
    "rm": cmd_rm,
    "remove": cmd_rm,
    "pending": cmd_pending,
    "surface": cmd_surface,
}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd = argv[1]
    if cmd not in COMMANDS:
        print(f"unknown command: {cmd}", file=sys.stderr)
        print("run with --help for usage", file=sys.stderr)
        return 2
    return COMMANDS[cmd](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
