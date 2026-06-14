"""Reproduce the lost-update race condition.

Important truth about CPython:
The GIL serializes Python bytecode execution and is only released at
checkpoints (every ~5 ms by default). For a tight `counter.x += 1`
loop, the read-modify-write almost always completes inside one GIL
hold — so the race is THEORETICALLY present but rarely manifests in
small demos. That is exactly what makes it dangerous in production:
the bug hides until load, scheduling, or a code change widens the
window.

This script proves the point by widening the window explicitly with
time.sleep(0) — a yield that lets the OS pick another thread between
the read and the write. Same logical operation, but now the bug is
unmissable.

Run:
    python race_demo.py             # narrow + stretched, side by side
    python race_demo.py 100000 8
"""
import sys
import threading
import time


class Counter:
    def __init__(self) -> None:
        self.x = 0


def increment_narrow(counter: Counter, n: int) -> None:
    """The natural pattern. Race exists, often hidden by GIL hold time."""
    for _ in range(n):
        counter.x += 1


def increment_stretched(counter: Counter, n: int) -> None:
    """Same logical operation, with the read-modify-write window opened
    wide by an explicit yield. This is what `x += 1` *could* look like
    under unfavorable scheduling — and across processes, in free-threaded
    Python, or in any language without a GIL, the window is always open.
    """
    for _ in range(n):
        val = counter.x      # READ
        time.sleep(0)        # yield — another thread can run here
        counter.x = val + 1  # WRITE (may clobber another thread's write)


def run(label: str, worker, n: int, threads: int) -> None:
    counter = Counter()
    workers = [threading.Thread(target=worker, args=(counter, n)) for _ in range(threads)]
    start = time.perf_counter()
    for t in workers: t.start()
    for t in workers: t.join()
    elapsed = time.perf_counter() - start
    expected = threads * n
    lost = expected - counter.x
    status = "OK " if lost == 0 else "LOST"
    print(
        f"[{status}] {label:<20} "
        f"expected={expected:>10,}  actual={counter.x:>10,}  "
        f"lost={lost:>10,}  ({lost / expected:.1%})  time={elapsed:.2f}s"
    )


def main(n: int, threads: int) -> None:
    # Encourage the interpreter to switch frequently. Default is 5ms.
    sys.setswitchinterval(1e-6)

    print(f"threads={threads}  N={n:,}  expected total={threads * n:,}\n")

    print("--- narrow window: usually hides the race ---")
    for _ in range(3):
        run("narrow", increment_narrow, n, threads)

    print("\n--- stretched window: race is unmissable ---")
    for _ in range(3):
        run("stretched", increment_stretched, n // 100, threads)
    print("\n(Stretched uses N/100 because sleep(0) is slow — the % lost is what matters.)")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    main(n, threads)
