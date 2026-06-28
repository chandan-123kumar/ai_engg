#!/usr/bin/env bash
# SessionStart hook for todo-keeper.
# Prints rate-limited pending TODOs as additional session context.
# Must complete fast (<500 ms) and must never break the session if it fails.

set -u

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="${PLUGIN_ROOT}/hooks/todo_cli.py"

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

if [ ! -f "${CLI}" ]; then
  exit 0
fi

# Hard timeout so a stuck script never blocks session start.
# `timeout` may not exist on macOS by default; fall back to plain invocation.
if command -v timeout >/dev/null 2>&1; then
  timeout 2s python3 "${CLI}" surface 2>/dev/null || true
elif command -v gtimeout >/dev/null 2>&1; then
  gtimeout 2s python3 "${CLI}" surface 2>/dev/null || true
else
  python3 "${CLI}" surface 2>/dev/null || true
fi

exit 0
