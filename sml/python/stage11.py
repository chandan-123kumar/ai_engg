# ============================================================
# STAGE 11 — Modules, Decorators, Generators
# ============================================================

# ---- MODULES ----

# Importing standard library
import math
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict

print(math.sqrt(16))
print(math.pi)
print(random.randint(1, 100))
print(datetime.now())
print(datetime.now() + timedelta(days=7))

# Counter — count occurrences
words = ["apple", "banana", "apple", "cherry", "banana", "apple"]
c = Counter(words)
print(c)                        # Counter({'apple': 3, 'banana': 2, ...})
print(c.most_common(2))         # top 2

# defaultdict — no KeyError on missing keys
dd = defaultdict(list)
dd["a"].append(1)
dd["a"].append(2)
dd["b"].append(3)
print(dict(dd))                 # {'a': [1, 2], 'b': [3]}

# ---- DECORATORS ----
# A decorator wraps a function to add behavior before/after it

import time
import functools

def timer(func):
    @functools.wraps(func)      # preserves original function metadata
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.4f}s")
        return result
    return wrapper

@timer
def slow_sum(n):
    return sum(range(n))

slow_sum(1000000)

# Decorator with arguments
def repeat(n):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def say(msg):
    print(msg)

say("hello")    # prints 3 times

# Stacking decorators (applied bottom-up)
@timer
@repeat(2)
def greet(name):
    print(f"Hi {name}")

greet("Alice")

# ---- GENERATORS ----
# Functions that yield values one at a time — lazy evaluation

def count_up(n):
    i = 0
    while i < n:
        yield i         # pauses here, resumes on next()
        i += 1

gen = count_up(5)
print(next(gen))        # 0
print(next(gen))        # 1
print(list(gen))        # [2, 3, 4] — consumes the rest

# Generators in for loops
for val in count_up(5):
    print(val, end=" ")
print()

# Infinite generator — only safe with generators, never with lists
def integers_from(n):
    while True:
        yield n
        n += 1

gen = integers_from(1)
print([next(gen) for _ in range(5)])    # [1, 2, 3, 4, 5]

# Real use case — process large file without loading into memory
def read_large_file(path):
    with open(path) as f:
        for line in f:
            yield line.strip()

# Generator with send() — two-way communication
def accumulator():
    total = 0
    while True:
        value = yield total     # yield current total, receive new value
        total += value

acc = accumulator()
next(acc)               # prime the generator
print(acc.send(10))     # 10
print(acc.send(20))     # 30
print(acc.send(5))      # 35

# ============================================================
# TASK:
#   1. Write a decorator `logger` that prints:
#      "calling <func_name> with args=... kwargs=..."
#      before the call and
#      "<func_name> returned <result>"
#      after
#   2. Write a generator `fibonacci()` that yields
#      Fibonacci numbers indefinitely
#   3. Use it to print the first 10 Fibonacci numbers
# ============================================================
