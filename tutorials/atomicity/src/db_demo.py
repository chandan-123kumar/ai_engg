"""Push the lock to the database — SQLite demo.

Compares the broken naive check-then-update (race condition) against the
atomic conditional UPDATE (no race possible). Same idea works on Postgres,
MySQL, etc. — the SQL is portable.

Run:
    python db_demo.py
"""
import os
import sqlite3
import sys
import threading
import time

DB_PATH = "/tmp/atomicity_demo.sqlite"

# Encourage thread switches mid-operation.
sys.setswitchinterval(1e-6)


def fresh_db(initial_stock: int) -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE inventory (id INTEGER PRIMARY KEY, stock INTEGER NOT NULL)")
    conn.execute("INSERT INTO inventory (id, stock) VALUES (1, ?)", (initial_stock,))
    conn.commit()
    conn.close()


# ---------- BROKEN: check in Python, then update -----------------------------
def buy_naive() -> bool:
    """Two round-trips with Python logic in between — race condition lives here."""
    conn = sqlite3.connect(DB_PATH, isolation_level=None)   # autocommit
    try:
        row = conn.execute("SELECT stock FROM inventory WHERE id = 1").fetchone()
        if row[0] < 1:
            return False
        # Gap: another thread can pass the same check before we update.
        time.sleep(0)
        conn.execute("UPDATE inventory SET stock = stock - 1 WHERE id = 1")
        return True
    finally:
        conn.close()


# ---------- FIXED: atomic conditional UPDATE ---------------------------------
def buy_atomic() -> bool:
    """One statement. The WHERE predicate and the SET happen under a row lock
    the database holds for the duration of the statement. No interleaving."""
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    try:
        cur = conn.execute(
            "UPDATE inventory SET stock = stock - 1 WHERE id = 1 AND stock >= 1"
        )
        return cur.rowcount == 1
    finally:
        conn.close()


# ---------- FIXED: explicit transaction with BEGIN IMMEDIATE -----------------
# SQLite's equivalent of "SELECT ... FOR UPDATE" — locks the database for
# writing as soon as the transaction begins, so the check and update are
# serialized w.r.t. other writers.
def buy_for_update() -> bool:
    conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=30)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT stock FROM inventory WHERE id = 1").fetchone()
        if row[0] < 1:
            conn.execute("ROLLBACK")          # NO write happened
            return False
        conn.execute("UPDATE inventory SET stock = stock - 1 WHERE id = 1")
        conn.execute("COMMIT")
        return True
    finally:
        conn.close()


# ---------- runner -----------------------------------------------------------
def run(label: str, buy_fn, customers: int, attempts_per_customer: int, initial_stock: int) -> None:
    fresh_db(initial_stock)
    sold = [0]
    sold_lock = threading.Lock()

    def shopper():
        local = 0
        for _ in range(attempts_per_customer):
            if buy_fn():
                local += 1
        with sold_lock:
            sold[0] += local

    start = time.perf_counter()
    ts = [threading.Thread(target=shopper) for _ in range(customers)]
    for t in ts: t.start()
    for t in ts: t.join()
    elapsed = time.perf_counter() - start

    final = sqlite3.connect(DB_PATH).execute("SELECT stock FROM inventory WHERE id = 1").fetchone()[0]
    over = sold[0] - initial_stock
    status = "OVERSOLD" if over > 0 else "ok"
    print(
        f"  [{label:<20}] sold={sold[0]:>3}  remaining={final:>3}  "
        f"({status}{' by ' + str(over) if over > 0 else ''})  "
        f"time={elapsed:.2f}s"
    )


def main() -> None:
    customers, attempts, stock = 16, 10, 50
    print(f"setup: stock={stock}, {customers} threads × {attempts} attempts = {customers * attempts} requests\n")

    print("BROKEN — Python check, then UPDATE (two round-trips):")
    for _ in range(3):
        run("naive", buy_naive, customers, attempts, stock)

    print("\nFIXED — atomic conditional UPDATE (one statement):")
    for _ in range(3):
        run("atomic UPDATE", buy_atomic, customers, attempts, stock)

    print("\nFIXED — BEGIN IMMEDIATE transaction (SQLite's SELECT FOR UPDATE):")
    for _ in range(3):
        run("BEGIN IMMEDIATE", buy_for_update, customers, attempts, stock)

    print("\nTakeaway:")
    print("  Naive 'check in Python then UPDATE' races even when the storage is a")
    print("  database — the race lives in the gap between the two round-trips,")
    print("  not in the database itself. Push the check INTO the UPDATE statement,")
    print("  or hold a real DB lock for the duration of the critical section.")


if __name__ == "__main__":
    main()
