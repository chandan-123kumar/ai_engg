"""Three real-world shapes of the lost-update bug.

Each scenario runs twice: BROKEN (no lock) and FIXED (lock or atomic).
The numbers tell the story.

Run:
    python use_cases.py
"""
import sys
import threading
import time
from collections import defaultdict

# Encourage the interpreter to switch frequently so the races
# show up reliably on modern CPython under the GIL.
sys.setswitchinterval(1e-6)


# =============================================================================
# Case 1 — Rate limiter that lets through too many requests
# =============================================================================
# A naive per-user request counter checks the count, then increments. Under
# concurrency, two threads can each read "9 < 10 = ok" and both increment
# to 10 → 11 requests admitted against a 10-request limit.

class NaiveRateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.counts: dict[str, int] = defaultdict(int)

    def allow(self, user: str) -> bool:
        if self.counts[user] >= self.limit:
            return False
        # gap: another thread can pass the check too
        time.sleep(0)
        self.counts[user] += 1
        return True


class LockedRateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.counts: dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()

    def allow(self, user: str) -> bool:
        with self.lock:
            if self.counts[user] >= self.limit:
                return False
            self.counts[user] += 1
            return True


def run_rate_limiter(limiter, threads: int, attempts_per_thread: int) -> int:
    admitted = [0]
    admit_lock = threading.Lock()

    def worker():
        local = 0
        for _ in range(attempts_per_thread):
            if limiter.allow("alice"):
                local += 1
        with admit_lock:
            admitted[0] += local

    ts = [threading.Thread(target=worker) for _ in range(threads)]
    for t in ts: t.start()
    for t in ts: t.join()
    return admitted[0]


def demo_rate_limiter() -> None:
    print("=" * 72)
    print("CASE 1 — Rate limiter (limit=100, 8 threads x 50 attempts)")
    print("=" * 72)
    limit = 100

    admitted = run_rate_limiter(NaiveRateLimiter(limit), threads=8, attempts_per_thread=50)
    print(f"  BROKEN: admitted={admitted}  (allowed limit was {limit})")
    print(f"          → {admitted - limit} requests slipped through" if admitted > limit else "          (got lucky this run)")

    admitted = run_rate_limiter(LockedRateLimiter(limit), threads=8, attempts_per_thread=50)
    print(f"  FIXED:  admitted={admitted}  (allowed limit was {limit}) ✓")


# =============================================================================
# Case 2 — Inventory oversell
# =============================================================================
# Online store decrements stock when a customer buys. Two checkouts hitting
# the last unit at the same time can BOTH succeed → oversold by one, customer
# either gets a refund-and-apology email or you ship from another warehouse
# at a loss.

class NaiveInventory:
    def __init__(self, stock: int) -> None:
        self.stock = stock

    def buy(self, qty: int = 1) -> bool:
        if self.stock < qty:
            return False
        time.sleep(0)               # gap between check and decrement
        self.stock -= qty
        return True


class LockedInventory:
    def __init__(self, stock: int) -> None:
        self.stock = stock
        self.lock = threading.Lock()

    def buy(self, qty: int = 1) -> bool:
        with self.lock:
            if self.stock < qty:
                return False
            self.stock -= qty
            return True


def run_inventory(inv, customers: int, attempts: int = 20) -> tuple[int, int]:
    """Each shopper retries up to `attempts` times — models real checkout
    pages where multiple users hammer the last few units."""
    sold = [0]
    sold_lock = threading.Lock()

    def shopper():
        local = 0
        for _ in range(attempts):
            if inv.buy(1):
                local += 1
        with sold_lock:
            sold[0] += local

    ts = [threading.Thread(target=shopper) for _ in range(customers)]
    for t in ts: t.start()
    for t in ts: t.join()
    return sold[0], inv.stock


def demo_inventory() -> None:
    print("\n" + "=" * 72)
    print("CASE 2 — Inventory oversell (stock=50, 200 concurrent shoppers)")
    print("=" * 72)

    sold, remaining = run_inventory(NaiveInventory(50), customers=200)
    overshoot = sold - 50
    print(f"  BROKEN: sold={sold}  remaining={remaining}")
    if overshoot > 0:
        print(f"          → OVERSOLD by {overshoot} units (refund-and-apology email time)")

    sold, remaining = run_inventory(LockedInventory(50), customers=200)
    print(f"  FIXED:  sold={sold}  remaining={remaining}  ✓")


# =============================================================================
# Case 3 — Concurrent bank transfers losing money
# =============================================================================
# Transfer = (read source, read dest, write source, write dest). With no
# synchronization, parallel transfers cause read-modify-write races that
# silently destroy or duplicate money. Total balance across all accounts
# must always equal initial total — if it doesn't, the ledger is wrong.

class NaiveBank:
    def __init__(self, accounts: dict[str, int]) -> None:
        self.accounts = dict(accounts)

    def transfer(self, src: str, dst: str, amount: int) -> bool:
        if self.accounts[src] < amount:
            return False
        src_new = self.accounts[src] - amount
        time.sleep(0)
        dst_new = self.accounts[dst] + amount
        time.sleep(0)
        self.accounts[src] = src_new
        self.accounts[dst] = dst_new
        return True

    def total(self) -> int:
        return sum(self.accounts.values())


class LockedBank:
    """Single global lock — simple, correct, fine for low contention."""

    def __init__(self, accounts: dict[str, int]) -> None:
        self.accounts = dict(accounts)
        self.lock = threading.Lock()

    def transfer(self, src: str, dst: str, amount: int) -> bool:
        with self.lock:
            if self.accounts[src] < amount:
                return False
            self.accounts[src] -= amount
            self.accounts[dst] += amount
            return True

    def total(self) -> int:
        with self.lock:
            return sum(self.accounts.values())


def run_bank(bank, transfers: int, threads: int) -> None:
    import random
    accounts = list(bank.accounts.keys())

    def worker():
        rng = random.Random()
        for _ in range(transfers):
            a, b = rng.sample(accounts, 2)
            bank.transfer(a, b, rng.randint(1, 50))

    ts = [threading.Thread(target=worker) for _ in range(threads)]
    for t in ts: t.start()
    for t in ts: t.join()


def demo_bank() -> None:
    print("\n" + "=" * 72)
    print("CASE 3 — Bank transfers (4 accounts of $1000 each = $4000 total)")
    print("=" * 72)
    initial = {"alice": 1000, "bob": 1000, "carol": 1000, "dave": 1000}
    expected_total = sum(initial.values())

    bank = NaiveBank(initial)
    run_bank(bank, transfers=500, threads=8)
    delta = bank.total() - expected_total
    print(f"  BROKEN: final total=${bank.total()}  (expected ${expected_total})")
    if delta != 0:
        sign = "+" if delta > 0 else ""
        print(f"          → money {('created' if delta > 0 else 'destroyed')}: {sign}${delta}")
        print(f"          balances: {bank.accounts}")

    bank = LockedBank(initial)
    run_bank(bank, transfers=500, threads=8)
    print(f"  FIXED:  final total=${bank.total()}  (expected ${expected_total}) ✓")
    print(f"          balances: {bank.accounts}")


# =============================================================================
def main() -> None:
    demo_rate_limiter()
    demo_inventory()
    demo_bank()
    print("\n" + "-" * 72)
    print("Same bug, three different domains, three different blast radii:")
    print("  - rate limiter:   wrong traffic shape, capacity surprises")
    print("  - inventory:      real money lost on refunds + customer trust")
    print("  - bank ledger:    money disappears or appears from nowhere")
    print("The fix is the same shape in every case: lock the read-modify-write.")


if __name__ == "__main__":
    main()
