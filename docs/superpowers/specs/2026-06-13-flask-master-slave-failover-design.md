# Flask Master/Slave Failover Demo — Design

**Date:** 2026-06-13
**Status:** Spec (pre-implementation)
**Goal:** A learning-focused demonstration of the master-slave (active-passive) failover pattern using three small Flask processes, where clients see a single fixed endpoint and traffic transparently fails over from master to slave when master dies, then fails back when master recovers.

---

## 1. Scope and non-goals

**In scope**
- Three Flask processes on localhost simulating a VIP-fronted master/slave pair.
- Single client-facing endpoint (`http://localhost:8000`).
- Automatic failure detection of the active backend via health checks.
- Automatic failover to the slave and automatic failback to the master.
- Observability through stdout logs and a status endpoint.

**Out of scope (explicit non-goals)**
- Real OS-level VIP (keepalived/VRRP/cloud LB).
- Replicated application state — backends are stateless.
- Proxy high availability — if the proxy process itself dies, the demo is down. Mitigating this would require a second proxy and a real VIP, which defeats the simplicity goal.
- Production hardening: TLS, auth, rate limiting, retries, circuit breakers.
- Multi-slave / N-replica setups.

---

## 2. Architecture

Three independent Python processes on localhost. Each is a small Flask app.

| Process  | Port   | Role |
|----------|--------|------|
| `proxy`  | `8000` | The "virtual IP." Single endpoint clients talk to. Forwards traffic to the currently-active backend. Runs a background health-checker. |
| `master` | `8001` | Primary backend. Receives traffic while healthy. |
| `slave`  | `8002` | Hot standby. Always running, only receives traffic when master is unhealthy. |

Master and slave are functionally identical — the same `backend.py` started twice with different `ROLE` and `PORT` env vars.

```
                       ┌──────────────────┐
   client ─── :8000 ──▶│      proxy       │
                       │  (forwarder +    │
                       │   health-checker)│
                       └────────┬─────────┘
                                │ forwards to "active"
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
           ┌──────────────┐            ┌──────────────┐
           │ master :8001 │            │ slave :8002  │
           └──────────────┘            └──────────────┘
                  ▲                           ▲
                  └── proxy pings /health ────┘
                       every 1s
```

---

## 3. Components

### 3.1 `backend.py` — the master/slave Flask app

One file, parameterized by env vars (`ROLE`, `PORT`). Run twice.

Endpoints:
- `GET /health` → `200 {"role": "<role>", "ok": true}`. Used by the proxy's health-checker.
- `GET /whoami` → `{"role": "<role>", "hostname": "<host>", "pid": <pid>}`. Lets a client see which backend served them.
- `GET /hello` → `{"message": "hello from <role>"}`. Trivial demo endpoint.

Stateless. No persistence. No shared storage.

### 3.2 `proxy.py` — the "virtual IP"

Flask app on `:8000`. Two responsibilities:

**Forwarder.** Every request whose path does *not* start with `/proxy/` is forwarded (via the `requests` library) to the currently-active backend. Method, path, query string, headers, and body are passed through; the upstream response (status, headers, body) is returned to the client.

**Status surface.**
- `GET /proxy/status` → JSON:
  ```json
  {
    "active": "master",
    "master_healthy": true,
    "slave_healthy": true,
    "last_failover_at": "2026-06-13T10:00:02Z",
    "last_failback_at": "2026-06-13T10:00:08Z"
  }
  ```
- No manual failover/failback endpoints — both are fully automatic.

### 3.3 Health-checker (background thread inside proxy)

A `threading.Thread` started at proxy boot. Loop:
1. Sleep 1s.
2. `GET /health` on master with a 500ms timeout.
3. `GET /health` on slave with a 500ms timeout.
4. Update per-backend state machine.
5. Re-evaluate `active`.

Per-backend state machine (hysteresis to prevent flapping):
- Each backend tracks `consecutive_misses` and `consecutive_hits`.
- `healthy → unhealthy` after **2 consecutive misses**.
- `unhealthy → healthy` after **2 consecutive hits**.
- Successful check resets miss counter; failed check resets hit counter.

`active` selection rule (evaluated after every state update):
- If master is healthy → `active = "master"`.
- Else if slave is healthy → `active = "slave"`.
- Else `active` is unchanged (last-known); requests will fail with 503 because the forwarder also checks health before forwarding.

State transitions are logged to stdout:
```
[proxy] FAILOVER: master → slave (master unhealthy)
[proxy] FAILBACK: slave → master (master healthy again)
```

### 3.4 `run.sh` — launcher

A small shell script that starts all three processes in the background, prefixes each line of stdout with `[proxy] / [master] / [slave]`, and traps `SIGINT` to clean up all three. Lets you `Ctrl-C` master from a separate terminal (`kill <pid>`) and watch the failover narrative in one place.

---

## 4. Data flow

### 4.1 Normal request (master healthy)
```
client ──GET /hello──▶ proxy:8000
                        active = "master"
                        ▼
                       master:8001 ──▶ "hello from master"
client ◀─── response ───
```

### 4.2 Background health checks (always running)
Every 1s the proxy pings `GET /health` on both backends with a 500ms timeout. Each ping updates the corresponding backend's miss/hit counters.

### 4.3 Failover timeline (master dies at t=0)
| Time     | Event |
|----------|-------|
| `t=0.0s` | Master process killed. |
| `0–1.0s` | Proxy still forwards to master. Client requests see connection errors. |
| `t=1.0s` | Health check #1 fails → `master.misses = 1`. Still considered healthy. |
| `t=2.0s` | Health check #2 fails → `master.misses = 2` → master = **UNHEALTHY**. Active flips to slave. Log `FAILOVER`. Stamp `last_failover_at`. |
| `t>2.0s` | All requests succeed via slave. |

Worst-case detection ≈ 2 seconds.

### 4.4 Failback timeline (master restarts)
- Master process restarted.
- Next health check succeeds → `master.hits = 1`. Still unhealthy.
- Following check (1s later) succeeds → `master.hits = 2` → master = **HEALTHY**. Active flips back to master. Log `FAILBACK`. Stamp `last_failback_at`.

### 4.5 Concurrency model
Shared state (`active`, per-backend health flags, counters, timestamps) lives in a single object guarded by a `threading.Lock`. The forwarder reads `active` under the lock for each request (cheap). The health-checker writes under the lock when state flips. No race condition on which backend serves a given request.

The client experiences:
- ~0–2s of failures during the detection window when master dies mid-traffic.
- After detection, requests succeed via slave.
- We do **not** transparently retry the failed in-flight request on the standby. Keeping failover visible to the client is the whole point of the demo.

---

## 5. Error handling

**Proxy → backend forwarding errors.** Any exception, timeout, or upstream 5xx during a real request returns `502 Bad Gateway` with body `{"error": "upstream unavailable", "active": "<role>"}`. The forwarder does *not* attempt a retry on the standby — that authority belongs solely to the health-checker, ensuring a single source of truth for which backend is active.

**Health-check errors.** Non-200, exception, or timeout counts as a miss. Resets the hit counter. Symmetric on the success side. Fixed 1s cadence, no backoff.

**Both backends unhealthy.** Proxy returns `503 Service Unavailable` with `{"error": "no healthy backend"}`. The health-checker keeps probing; whichever recovers first becomes active.

**Failback while requests are in flight to slave.** When master is promoted back, in-flight requests already routed to slave complete normally. Only *new* requests are routed to master.

**Proxy crash.** Not handled. Documented as a known limitation in section 1.

---

## 6. Testing

### 6.1 Manual smoke test
1. Start everything via `run.sh`.
2. `curl http://localhost:8000/whoami` → expect `role: master`.
3. Kill master process (`kill $(pgrep -f 'ROLE=master')`).
4. Wait ~2s.
5. `curl http://localhost:8000/whoami` → expect `role: slave`.
6. Restart master.
7. Wait ~2s.
8. `curl http://localhost:8000/whoami` → expect `role: master` again.

### 6.2 Live status observation
In a second terminal:
```
watch -n 0.5 curl -s http://localhost:8000/proxy/status
```
Kill/restart master while watching. Expect `active` to flip and `last_failover_at` / `last_failback_at` to update.

### 6.3 Automated pytest (light)
One test file. Spin up two fake backends (Flask test clients or the `pytest-httpserver` fixture) and start the proxy pointed at them.

- `test_proxy_forwards_to_master_when_healthy` — assert response identifies master.
- `test_proxy_fails_over_when_master_down` — stop the fake master, wait for detection, assert proxy now routes to slave; restart master, wait, assert failback.

We do **not** write exhaustive unit tests for the state machine — the integration tests cover its behavior end-to-end, and the code is small enough to read in one sitting.

---

## 7. File layout

```
communication_mode/
├── backend.py        # the master/slave Flask app
├── proxy.py          # the "VIP" with forwarder + health-checker
├── run.sh            # launcher for all three processes
├── requirements.txt  # flask, requests, pytest, pytest-httpserver
└── tests/
    └── test_failover.py
```

---

## 8. Configuration

All ports and timings are constants at the top of `proxy.py` and `backend.py`. No config file. Override via env vars only where it matters:
- `backend.py`: `ROLE` (`master` | `slave`), `PORT`.
- `proxy.py`: hardcoded `MASTER_URL=http://localhost:8001`, `SLAVE_URL=http://localhost:8002`.

Tuning constants (in `proxy.py`):
- `HEALTH_INTERVAL_S = 1.0`
- `HEALTH_TIMEOUT_S  = 0.5`
- `FAIL_THRESHOLD    = 2`
- `RECOVER_THRESHOLD = 2`

