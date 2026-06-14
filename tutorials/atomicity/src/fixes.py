"""Five ways to make a counter safe under concurrent increments, with timing.

Run:
    python fixes.py            # default N=1_000_000
    python fixes.py 5000000
"""
import sys
import threading
import time
from itertools import count


# ---------- 1. threading.Lock ------------------------------------------------
def with_lock(n: int) -> int:
    state = [0]
    lock = threading.Lock()

    def worker():
        for _ in range(n):
            with lock:
                state[0] += 1

    return _run_two_threads(worker, state)


# ---------- 2. itertools.count (atomic at the C level) -----------------------
def with_itertools_count(n: int) -> int:
    counter = count()

    def worker():
        for _ in range(n):
            next(counter)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads: t.start()
    for t in threads: t.join()
    # itertools.count has no read accessor; consume one more to see current
    return next(counter)


# ---------- 3. Local sum, then one locked merge ------------------------------
def with_local_then_merge(n: int) -> int:
    state = [0]
    lock = threading.Lock()

    def worker():
        local = 0
        for _ in range(n):
            local += 1
        with lock:
            state[0] += local

    return _run_two_threads(worker, state)


# ---------- 4. threading.Lock around a batch ---------------------------------
def with_batched_lock(n: int, batch: int = 1000) -> int:
    state = [0]
    lock = threading.Lock()

    def worker():
        remaining = n
        while remaining:
            chunk = min(batch, remaining)
            with lock:
                state[0] += chunk
            remaining -= chunk

    return _run_two_threads(worker, state)


# ---------- 5. queue.Queue (serialize via a single owner) --------------------
def with_queue(n: int) -> int:
    import queue
    q: queue.Queue = queue.Queue()
    state = [0]

    def producer():
        for _ in range(n):
            q.put(1)

    def consumer():
        seen = 0
        target = 2 * n
        while seen < target:
            state[0] += q.get()
            seen += 1

    threads = [
        threading.Thread(target=producer),
        threading.Thread(target=producer),
        threading.Thread(target=consumer),
    ]
    for t in threads: t.start()
    for t in threads: t.join()
    return state[0]


# -----------------------------------------------------------------------------
def _run_two_threads(worker, state) -> int:
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start(); t2.start()
    t1.join(); t2.join()
    return state[0]


def time_it(name: str, fn, n: int) -> None:
    start = time.perf_counter()
    result = fn(n)
    elapsed = time.perf_counter() - start
    expected = 2 * n
    status = "OK " if result == expected else "BAD"
    print(f"[{status}] {name:<28} result={result:>12,}  time={elapsed:6.2f}s")


def main(n: int) -> None:
    print(f"expected = {2 * n:,}\n")
    time_it("threading.Lock (per op)",  with_lock, n)
    time_it("itertools.count",          with_itertools_count, n)
    time_it("local sum + merge",        with_local_then_merge, n)
    time_it("batched lock (size 1000)", with_batched_lock, n)
    time_it("queue.Queue",              with_queue, n)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    main(n)
