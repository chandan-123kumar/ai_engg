# Flask Master/Slave Failover Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-process learning demo (proxy + master + slave Flask apps) that demonstrates automatic master→slave failover and master→master failback behind a single fixed endpoint.

**Architecture:** A Flask proxy on `:8000` forwards every request to a "currently-active" backend. A background thread inside the proxy pings `/health` on master (`:8001`) and slave (`:8002`) every 1 second; after 2 consecutive failures the active target flips, after 2 consecutive successes it flips back. Backends are identical stateless Flask apps differentiated by a `ROLE` env var.

**Tech Stack:** Python 3.11+, Flask, requests, pytest, pytest-httpserver.

**Spec:** `docs/superpowers/specs/2026-06-13-flask-master-slave-failover-design.md`

---

## File Structure

```
communication_mode/
├── backend.py            # master/slave Flask app (run twice with different env)
├── proxy.py              # proxy app: HealthState + checker thread + forwarder + /proxy/status
├── run.sh                # launcher: starts all 3 procs with prefixed logs
├── requirements.txt
└── tests/
    ├── __init__.py
    ├── test_backend.py        # unit tests for backend endpoints
    ├── test_health_state.py   # unit tests for the HealthState class
    └── test_failover.py       # integration: real proxy + fake backends, kill/restart
```

**Design note:** `proxy.py` is one file but internally split into a `HealthState` class (testable in isolation), a `health_checker_loop()` function, and the Flask routes. Keeps the spec's "one file" requirement while making the state machine independently unit-testable.

---

## Task 1: Project skeleton

**Files:**
- Create: `communication_mode/requirements.txt`
- Create: `communication_mode/tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

Create `communication_mode/requirements.txt`:
```
flask==3.0.3
requests==2.32.3
pytest==8.3.3
pytest-httpserver==1.1.0
```

- [ ] **Step 2: Create empty tests package**

Create `communication_mode/tests/__init__.py` (empty file).

- [ ] **Step 3: Install dependencies and verify**

Run from `communication_mode/`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "import flask, requests, pytest, pytest_httpserver; print('ok')"
```
Expected output: `ok`

- [ ] **Step 4: Commit**

```bash
git add communication_mode/requirements.txt communication_mode/tests/__init__.py
git commit -m "chore: project skeleton for failover demo"
```

---

## Task 2: backend.py — `/health` endpoint (TDD)

**Files:**
- Create: `communication_mode/backend.py`
- Create: `communication_mode/tests/test_backend.py`

- [ ] **Step 1: Write the failing test**

Create `communication_mode/tests/test_backend.py`:
```python
import os
import pytest
from communication_mode.backend import create_app


@pytest.fixture
def client_master():
    os.environ["ROLE"] = "master"
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_health_returns_role_and_ok(client_master):
    resp = client_master.get("/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"role": "master", "ok": True}
```

- [ ] **Step 2: Run test to verify it fails**

From the repo root (parent of `communication_mode/`):
```bash
pytest communication_mode/tests/test_backend.py::test_health_returns_role_and_ok -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'communication_mode.backend'`.

- [ ] **Step 3: Write minimal implementation**

Create `communication_mode/backend.py`:
```python
import os
from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)
    role = os.environ.get("ROLE", "master")

    @app.get("/health")
    def health():
        return jsonify({"role": role, "ok": True})

    return app
```

Also create `communication_mode/__init__.py` (empty) so `communication_mode.backend` is importable.

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest communication_mode/tests/test_backend.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add communication_mode/backend.py communication_mode/__init__.py communication_mode/tests/test_backend.py
git commit -m "feat(backend): add /health endpoint with role"
```

---

## Task 3: backend.py — `/whoami` and `/hello` endpoints (TDD)

**Files:**
- Modify: `communication_mode/backend.py`
- Modify: `communication_mode/tests/test_backend.py`

- [ ] **Step 1: Add failing tests**

Append to `communication_mode/tests/test_backend.py`:
```python
def test_whoami_returns_role_hostname_pid(client_master):
    resp = client_master.get("/whoami")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["role"] == "master"
    assert isinstance(body["hostname"], str) and body["hostname"]
    assert isinstance(body["pid"], int) and body["pid"] > 0


def test_hello_returns_message_with_role(client_master):
    resp = client_master.get("/hello")
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "hello from master"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest communication_mode/tests/test_backend.py -v
```
Expected: 2 FAIL (404 from Flask).

- [ ] **Step 3: Implement the endpoints**

Replace `communication_mode/backend.py` with:
```python
import os
import socket
from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)
    role = os.environ.get("ROLE", "master")

    @app.get("/health")
    def health():
        return jsonify({"role": role, "ok": True})

    @app.get("/whoami")
    def whoami():
        return jsonify({
            "role": role,
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
        })

    @app.get("/hello")
    def hello():
        return jsonify({"message": f"hello from {role}"})

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8001"))
    create_app().run(host="127.0.0.1", port=port, threaded=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest communication_mode/tests/test_backend.py -v
```
Expected: 3 PASS.

- [ ] **Step 5: Manual sanity check**

```bash
ROLE=master PORT=8001 python -m communication_mode.backend &
sleep 1
curl -s http://localhost:8001/whoami
curl -s http://localhost:8001/hello
kill %1
```
Expected: JSON with role=master, then `{"message":"hello from master"}`.

- [ ] **Step 6: Commit**

```bash
git add communication_mode/backend.py communication_mode/tests/test_backend.py
git commit -m "feat(backend): add /whoami and /hello endpoints"
```

---

## Task 4: HealthState class — failure transition (TDD)

The health state machine has hysteresis: 2 misses → unhealthy, 2 hits → healthy. Built as a standalone class for unit testing, then used by the background checker thread.

**Files:**
- Create: `communication_mode/proxy.py`
- Create: `communication_mode/tests/test_health_state.py`

- [ ] **Step 1: Write the failing test**

Create `communication_mode/tests/test_health_state.py`:
```python
from communication_mode.proxy import HealthState


def test_starts_healthy_and_active_is_master():
    s = HealthState()
    assert s.master_healthy is True
    assert s.slave_healthy is True
    assert s.active == "master"


def test_master_flips_unhealthy_after_two_misses_and_active_becomes_slave():
    s = HealthState()
    s.record("master", ok=True)  # healthy stays healthy
    s.record("master", ok=False)  # miss 1, still healthy
    assert s.master_healthy is True
    assert s.active == "master"
    s.record("master", ok=False)  # miss 2 → unhealthy
    assert s.master_healthy is False
    assert s.active == "slave"
    assert s.last_failover_at is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest communication_mode/tests/test_health_state.py -v
```
Expected: FAIL with `ImportError: cannot import name 'HealthState'`.

- [ ] **Step 3: Implement minimal HealthState**

Create `communication_mode/proxy.py`:
```python
import threading
from datetime import datetime, timezone
from typing import Optional

FAIL_THRESHOLD = 2
RECOVER_THRESHOLD = 2


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class HealthState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.master_healthy = True
        self.slave_healthy = True
        self._master_misses = 0
        self._master_hits = 0
        self._slave_misses = 0
        self._slave_hits = 0
        self.active = "master"
        self.last_failover_at: Optional[str] = None
        self.last_failback_at: Optional[str] = None

    def record(self, role: str, ok: bool) -> None:
        with self._lock:
            if role == "master":
                if ok:
                    self._master_hits += 1
                    self._master_misses = 0
                    if not self.master_healthy and self._master_hits >= RECOVER_THRESHOLD:
                        self.master_healthy = True
                else:
                    self._master_misses += 1
                    self._master_hits = 0
                    if self.master_healthy and self._master_misses >= FAIL_THRESHOLD:
                        self.master_healthy = False
            elif role == "slave":
                if ok:
                    self._slave_hits += 1
                    self._slave_misses = 0
                    if not self.slave_healthy and self._slave_hits >= RECOVER_THRESHOLD:
                        self.slave_healthy = True
                else:
                    self._slave_misses += 1
                    self._slave_hits = 0
                    if self.slave_healthy and self._slave_misses >= FAIL_THRESHOLD:
                        self.slave_healthy = False
            self._reevaluate_active()

    def _reevaluate_active(self) -> None:
        prev = self.active
        if self.master_healthy:
            new_active = "master"
        elif self.slave_healthy:
            new_active = "slave"
        else:
            new_active = prev
        if new_active != prev:
            self.active = new_active
            ts = _now_iso()
            if new_active == "slave":
                self.last_failover_at = ts
            elif new_active == "master":
                self.last_failback_at = ts

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "active": self.active,
                "master_healthy": self.master_healthy,
                "slave_healthy": self.slave_healthy,
                "last_failover_at": self.last_failover_at,
                "last_failback_at": self.last_failback_at,
            }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest communication_mode/tests/test_health_state.py -v
```
Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add communication_mode/proxy.py communication_mode/tests/test_health_state.py
git commit -m "feat(proxy): HealthState with failure transition"
```

---

## Task 5: HealthState — recovery / failback transition (TDD)

**Files:**
- Modify: `communication_mode/tests/test_health_state.py`

- [ ] **Step 1: Add failing tests**

Append to `communication_mode/tests/test_health_state.py`:
```python
def test_master_recovers_after_two_hits_and_active_flips_back():
    s = HealthState()
    s.record("master", ok=False)
    s.record("master", ok=False)  # master unhealthy, active=slave
    assert s.active == "slave"

    s.record("master", ok=True)  # hit 1, still unhealthy
    assert s.master_healthy is False
    assert s.active == "slave"

    s.record("master", ok=True)  # hit 2 → healthy → failback
    assert s.master_healthy is True
    assert s.active == "master"
    assert s.last_failback_at is not None


def test_single_miss_then_hit_does_not_flip():
    s = HealthState()
    s.record("master", ok=False)  # miss 1
    s.record("master", ok=True)   # resets, still healthy
    assert s.master_healthy is True
    assert s.active == "master"


def test_both_unhealthy_keeps_last_active():
    s = HealthState()
    s.record("master", ok=False)
    s.record("master", ok=False)  # active=slave
    s.record("slave", ok=False)
    s.record("slave", ok=False)   # slave also unhealthy
    assert s.master_healthy is False
    assert s.slave_healthy is False
    assert s.active == "slave"   # last known
```

- [ ] **Step 2: Run tests**

```bash
pytest communication_mode/tests/test_health_state.py -v
```
Expected: 5 PASS (no implementation change needed — Task 4's code already covers this; if any fails, fix and rerun).

- [ ] **Step 3: Commit**

```bash
git add communication_mode/tests/test_health_state.py
git commit -m "test(proxy): cover recovery and both-down state transitions"
```

---

## Task 6: Proxy forwarder route (TDD)

The forwarder takes any non-`/proxy/*` request and proxies it to the currently-active backend via the `requests` library.

**Files:**
- Modify: `communication_mode/proxy.py`
- Create: `communication_mode/tests/test_failover.py`

- [ ] **Step 1: Write the failing test**

Create `communication_mode/tests/test_failover.py`:
```python
import pytest
from pytest_httpserver import HTTPServer
from communication_mode.proxy import create_app, HealthState


@pytest.fixture
def state():
    return HealthState()


@pytest.fixture
def master_server():
    with HTTPServer() as server:
        yield server


@pytest.fixture
def slave_server():
    with HTTPServer() as server:
        yield server


@pytest.fixture
def proxy_client(state, master_server, slave_server):
    app = create_app(
        state=state,
        master_url=f"http://{master_server.host}:{master_server.port}",
        slave_url=f"http://{slave_server.host}:{slave_server.port}",
    )
    app.config["TESTING"] = True
    return app.test_client()


def test_forwards_to_master_when_active(proxy_client, master_server, state):
    master_server.expect_request("/hello").respond_with_json(
        {"message": "hello from master"}
    )
    assert state.active == "master"

    resp = proxy_client.get("/hello")
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "hello from master"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest communication_mode/tests/test_failover.py::test_forwards_to_master_when_active -v
```
Expected: FAIL with `ImportError: cannot import name 'create_app'`.

- [ ] **Step 3: Add `create_app` and forwarder**

Append to `communication_mode/proxy.py`:
```python
import requests
from flask import Flask, Response, jsonify, request


def create_app(
    state: "HealthState",
    master_url: str = "http://127.0.0.1:8001",
    slave_url: str = "http://127.0.0.1:8002",
) -> Flask:
    app = Flask(__name__)
    backends = {"master": master_url, "slave": slave_url}

    @app.route(
        "/<path:path>",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    def forward(path: str):
        if path.startswith("proxy/"):
            # /proxy/* is handled by explicit routes registered below
            return jsonify({"error": "not found"}), 404

        snap = state.snapshot()
        active = snap["active"]
        if not snap[f"{active}_healthy"]:
            return jsonify({"error": "no healthy backend"}), 503

        upstream = backends[active]
        url = f"{upstream}/{path}"
        try:
            r = requests.request(
                method=request.method,
                url=url,
                params=request.args,
                data=request.get_data(),
                headers={k: v for k, v in request.headers if k.lower() != "host"},
                timeout=5,
            )
        except requests.RequestException:
            return jsonify({"error": "upstream unavailable", "active": active}), 502

        excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
        headers = [(k, v) for k, v in r.headers.items() if k.lower() not in excluded]
        return Response(r.content, status=r.status_code, headers=headers)

    return app
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest communication_mode/tests/test_failover.py::test_forwards_to_master_when_active -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add communication_mode/proxy.py communication_mode/tests/test_failover.py
git commit -m "feat(proxy): forward requests to active backend"
```

---

## Task 7: Proxy fails over to slave when master is unhealthy (TDD)

**Files:**
- Modify: `communication_mode/tests/test_failover.py`

- [ ] **Step 1: Add failing test**

Append to `communication_mode/tests/test_failover.py`:
```python
def test_forwards_to_slave_after_master_marked_unhealthy(
    proxy_client, slave_server, state
):
    slave_server.expect_request("/hello").respond_with_json(
        {"message": "hello from slave"}
    )
    state.record("master", ok=False)
    state.record("master", ok=False)
    assert state.active == "slave"

    resp = proxy_client.get("/hello")
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "hello from slave"}


def test_returns_503_when_both_backends_unhealthy(proxy_client, state):
    state.record("master", ok=False)
    state.record("master", ok=False)
    state.record("slave", ok=False)
    state.record("slave", ok=False)

    resp = proxy_client.get("/hello")
    assert resp.status_code == 503
    assert resp.get_json() == {"error": "no healthy backend"}


def test_returns_502_when_active_backend_connection_fails(proxy_client, state):
    # both still marked healthy by state, but master_server fixture has no
    # matching expectation → pytest-httpserver returns 500. We rely on the
    # forwarder treating non-2xx as a normal response (passthrough), so this
    # test instead validates the exception path by pointing at a closed port.
    from communication_mode.proxy import create_app, HealthState

    s = HealthState()
    app = create_app(
        state=s,
        master_url="http://127.0.0.1:1",  # unroutable
        slave_url="http://127.0.0.1:2",
    )
    app.config["TESTING"] = True
    resp = app.test_client().get("/hello")
    assert resp.status_code == 502
    assert resp.get_json() == {"error": "upstream unavailable", "active": "master"}
```

- [ ] **Step 2: Run tests**

```bash
pytest communication_mode/tests/test_failover.py -v
```
Expected: 4 PASS (1 existing + 3 new).

- [ ] **Step 3: Commit**

```bash
git add communication_mode/tests/test_failover.py
git commit -m "test(proxy): cover failover, both-down, and 502 paths"
```

---

## Task 8: Proxy `/proxy/status` endpoint (TDD)

**Files:**
- Modify: `communication_mode/proxy.py`
- Modify: `communication_mode/tests/test_failover.py`

- [ ] **Step 1: Add failing test**

Append to `communication_mode/tests/test_failover.py`:
```python
def test_proxy_status_returns_snapshot(proxy_client, state):
    resp = proxy_client.get("/proxy/status")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "active": "master",
        "master_healthy": True,
        "slave_healthy": True,
        "last_failover_at": None,
        "last_failback_at": None,
    }


def test_proxy_status_reflects_failover(proxy_client, state):
    state.record("master", ok=False)
    state.record("master", ok=False)
    body = proxy_client.get("/proxy/status").get_json()
    assert body["active"] == "slave"
    assert body["master_healthy"] is False
    assert body["last_failover_at"] is not None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest communication_mode/tests/test_failover.py -v
```
Expected: 2 new FAIL (status route currently falls through to the `/<path:path>` forwarder).

- [ ] **Step 3: Register the status route BEFORE the catch-all**

Modify `create_app` in `communication_mode/proxy.py` — add the `/proxy/status` route **before** the `@app.route("/<path:path>", ...)` decorator:

```python
def create_app(
    state: "HealthState",
    master_url: str = "http://127.0.0.1:8001",
    slave_url: str = "http://127.0.0.1:8002",
) -> Flask:
    app = Flask(__name__)
    backends = {"master": master_url, "slave": slave_url}

    @app.get("/proxy/status")
    def proxy_status():
        return jsonify(state.snapshot())

    @app.route(
        "/<path:path>",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    def forward(path: str):
        # ... (body unchanged from Task 6)
```

(Keep the forward function body from Task 6.)

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest communication_mode/tests/test_failover.py -v
```
Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add communication_mode/proxy.py communication_mode/tests/test_failover.py
git commit -m "feat(proxy): add /proxy/status endpoint"
```

---

## Task 9: Background health-checker thread + proxy main

Wires the proxy together: starts the background thread, exposes the Flask app on `:8000`.

**Files:**
- Modify: `communication_mode/proxy.py`

- [ ] **Step 1: Add the health-checker loop and `__main__`**

Append to `communication_mode/proxy.py`:
```python
import logging
import time

HEALTH_INTERVAL_S = 1.0
HEALTH_TIMEOUT_S = 0.5

log = logging.getLogger("proxy")


def health_checker_loop(state: HealthState, master_url: str, slave_url: str, stop_event: threading.Event) -> None:
    while not stop_event.wait(HEALTH_INTERVAL_S):
        for role, url in (("master", master_url), ("slave", slave_url)):
            prev_active = state.active
            try:
                r = requests.get(f"{url}/health", timeout=HEALTH_TIMEOUT_S)
                ok = r.status_code == 200
            except requests.RequestException:
                ok = False
            state.record(role, ok)
            new_active = state.active
            if new_active != prev_active:
                if new_active == "slave":
                    log.warning("FAILOVER: master → slave (master unhealthy)")
                else:
                    log.warning("FAILBACK: slave → master (master healthy again)")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[proxy] %(message)s")
    master_url = "http://127.0.0.1:8001"
    slave_url = "http://127.0.0.1:8002"
    state = HealthState()
    stop = threading.Event()
    t = threading.Thread(
        target=health_checker_loop,
        args=(state, master_url, slave_url, stop),
        daemon=True,
    )
    t.start()
    app = create_app(state=state, master_url=master_url, slave_url=slave_url)
    try:
        app.run(host="127.0.0.1", port=8000, threaded=True)
    finally:
        stop.set()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify proxy starts standalone**

```bash
python -m communication_mode.proxy &
sleep 1
curl -s http://localhost:8000/proxy/status
# Expect: master/slave shown unhealthy after 2s because no backends are running
sleep 3
curl -s http://localhost:8000/proxy/status
kill %1
```
Expected (second curl): `master_healthy: false`, `slave_healthy: false`.

- [ ] **Step 3: Commit**

```bash
git add communication_mode/proxy.py
git commit -m "feat(proxy): background health-checker + main entrypoint"
```

---

## Task 10: `run.sh` launcher

**Files:**
- Create: `communication_mode/run.sh`

- [ ] **Step 1: Write the launcher**

Create `communication_mode/run.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Activate venv if present
if [[ -f communication_mode/.venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source communication_mode/.venv/bin/activate
fi

pids=()
cleanup() {
  echo "[run.sh] shutting down..."
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait || true
}
trap cleanup INT TERM EXIT

prefix() { sed -u "s/^/[$1] /"; }

ROLE=master PORT=8001 python -m communication_mode.backend 2>&1 | prefix master &
pids+=($!)

ROLE=slave PORT=8002 python -m communication_mode.backend 2>&1 | prefix slave &
pids+=($!)

python -m communication_mode.proxy 2>&1 | prefix proxy &
pids+=($!)

wait
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x communication_mode/run.sh
```

- [ ] **Step 3: Smoke test the launcher**

Open a second terminal. In terminal 1:
```bash
./communication_mode/run.sh
```
In terminal 2:
```bash
sleep 2
curl -s http://localhost:8000/whoami
# Expect: {"role":"master", ...}
kill "$(pgrep -f 'ROLE=master')"
sleep 3
curl -s http://localhost:8000/whoami
# Expect: {"role":"slave", ...}
```
Stop terminal 1 with `Ctrl-C`.

- [ ] **Step 4: Commit**

```bash
git add communication_mode/run.sh
git commit -m "feat: add run.sh launcher with prefixed logs"
```

---

## Task 11: Full-system integration test

Spawns the **real** proxy and two **real** backends as subprocesses, then exercises a full failover/failback cycle through the proxy.

**Files:**
- Modify: `communication_mode/tests/test_failover.py`

- [ ] **Step 1: Add the end-to-end test**

Append to `communication_mode/tests/test_failover.py`:
```python
import os
import signal
import subprocess
import sys
import time
import requests as http


def _wait_for(url: str, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if http.get(url, timeout=0.5).status_code == 200:
                return
        except http.RequestException:
            pass
        time.sleep(0.1)
    raise AssertionError(f"{url} did not come up within {timeout}s")


def _spawn(args, env=None):
    return subprocess.Popen(
        [sys.executable, "-m", *args],
        env={**os.environ, **(env or {})},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_end_to_end_failover_and_failback():
    master = _spawn(["communication_mode.backend"], env={"ROLE": "master", "PORT": "8001"})
    slave = _spawn(["communication_mode.backend"], env={"ROLE": "slave", "PORT": "8002"})
    _wait_for("http://127.0.0.1:8001/health")
    _wait_for("http://127.0.0.1:8002/health")

    proxy = _spawn(["communication_mode.proxy"])
    _wait_for("http://127.0.0.1:8000/proxy/status")

    try:
        # Initially active = master
        body = http.get("http://127.0.0.1:8000/whoami", timeout=1).json()
        assert body["role"] == "master"

        # Kill master, wait for detection (~2s), expect slave to serve
        master.send_signal(signal.SIGTERM)
        master.wait(timeout=3)
        time.sleep(3.0)
        body = http.get("http://127.0.0.1:8000/whoami", timeout=1).json()
        assert body["role"] == "slave"

        status = http.get("http://127.0.0.1:8000/proxy/status", timeout=1).json()
        assert status["active"] == "slave"
        assert status["last_failover_at"] is not None

        # Restart master, wait for failback
        master = _spawn(["communication_mode.backend"], env={"ROLE": "master", "PORT": "8001"})
        _wait_for("http://127.0.0.1:8001/health")
        time.sleep(3.0)
        body = http.get("http://127.0.0.1:8000/whoami", timeout=1).json()
        assert body["role"] == "master"
        status = http.get("http://127.0.0.1:8000/proxy/status", timeout=1).json()
        assert status["last_failback_at"] is not None
    finally:
        for p in (proxy, master, slave):
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()
```

- [ ] **Step 2: Run the end-to-end test**

```bash
pytest communication_mode/tests/test_failover.py::test_end_to_end_failover_and_failback -v
```
Expected: PASS in ~10 seconds.

- [ ] **Step 3: Run the full test suite**

```bash
pytest communication_mode/tests -v
```
Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add communication_mode/tests/test_failover.py
git commit -m "test: end-to-end failover and failback through real subprocesses"
```

---

## Done

You have:
- Two identical Flask backends (master `:8001`, slave `:8002`).
- A proxy on `:8000` that forwards to whichever backend is healthy, with automatic failover (~2s) and failback.
- Logs and a `/proxy/status` endpoint for observability.
- Unit tests for `HealthState`, integration tests for the proxy forwarder, and a real-subprocess end-to-end test.
- `run.sh` to demo it interactively.
