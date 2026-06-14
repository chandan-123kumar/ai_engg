"""Race condition across PROCESSES (no GIL between them).

multiprocessing.Value with a lock makes increments atomic across processes.

Run:
    python process_demo.py
"""
import multiprocessing as mp


def worker_no_lock(shared, n):
    for _ in range(n):
        shared.value += 1   # NOT atomic: read, add, write


def worker_with_lock(shared, lock, n):
    for _ in range(n):
        with lock:
            shared.value += 1


def main():
    n = 200_000

    # Unsafe
    shared = mp.Value("i", 0, lock=False)
    procs = [mp.Process(target=worker_no_lock, args=(shared, n)) for _ in range(2)]
    for p in procs: p.start()
    for p in procs: p.join()
    print(f"no lock:   expected={2*n:,}  actual={shared.value:,}  lost={2*n - shared.value:,}")

    # Safe
    shared = mp.Value("i", 0, lock=False)
    lock = mp.Lock()
    procs = [mp.Process(target=worker_with_lock, args=(shared, lock, n)) for _ in range(2)]
    for p in procs: p.start()
    for p in procs: p.join()
    print(f"with lock: expected={2*n:,}  actual={shared.value:,}  lost={2*n - shared.value:,}")


if __name__ == "__main__":
    main()
