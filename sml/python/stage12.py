# ============================================================
# STAGE 12 — Advanced: typing, dataclasses, itertools, and more
# ============================================================

# ---- TYPE HINTS (Python 3.9+) ----
# Not enforced at runtime, but great for readability & tooling

def greet(name: str, times: int = 1) -> str:
    return (name + " ") * times

def process(items: list[int]) -> dict[str, int]:
    return {"sum": sum(items), "count": len(items)}

# Union types
def parse(val: str | int) -> int:
    return int(val)

# Optional (can be None)
def find(items: list[str], target: str) -> str | None:
    return target if target in items else None

print(greet("Hello", 3))
print(process([1, 2, 3, 4]))
print(find(["a", "b"], "c"))    # None

# ---- DATACLASSES ----
# Auto-generates __init__, __repr__, __eq__ from field annotations

from dataclasses import dataclass, field

@dataclass
class Point:
    x: float
    y: float

    def distance(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5

p1 = Point(3, 4)
p2 = Point(3, 4)
print(p1)           # Point(x=3, y=4)  — free __repr__
print(p1 == p2)     # True             — free __eq__
print(p1.distance())

# frozen=True makes it immutable (and hashable — usable as dict key)
@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

# default_factory for mutable defaults
@dataclass
class Team:
    name: str
    members: list[str] = field(default_factory=list)   # NOT members=[] !!

t = Team("Dev")
t.members.append("Alice")
print(t)

# ---- ITERTOOLS ----
import itertools

# chain — flatten iterables
print(list(itertools.chain([1,2], [3,4], [5])))    # [1,2,3,4,5]

# islice — slice a generator/iterator
gen = (x**2 for x in itertools.count(1))           # infinite squares
print(list(itertools.islice(gen, 5)))               # [1,4,9,16,25]

# groupby — group consecutive items
from itertools import groupby
data = [("a", 1), ("a", 2), ("b", 3), ("b", 4), ("a", 5)]
for key, group in groupby(data, key=lambda x: x[0]):
    print(key, list(group))

# combinations & permutations
print(list(itertools.combinations("ABC", 2)))       # [('A','B'),('A','C'),('B','C')]
print(list(itertools.permutations("AB", 2)))        # [('A','B'),('B','A')]

# ---- CONTEXT MANAGERS with contextlib ----
from contextlib import contextmanager

@contextmanager
def managed_resource(name: str):
    print(f"acquiring {name}")
    try:
        yield name.upper()
    finally:
        print(f"releasing {name}")

with managed_resource("database") as res:
    print(f"using {res}")

# ---- WALRUS OPERATOR := (Python 3.8+) ----
# Assign and use in same expression
import re
text = "Order #12345 confirmed"
if m := re.search(r"#(\d+)", text):
    print(f"Order ID: {m.group(1)}")   # 12345

# In while loops — common pattern
data = [1, 2, 3, 4, 5]
while chunk := data[:2]:
    print(chunk)
    data = data[2:]

# ---- __slots__ — memory optimization for classes ----
class Normal:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Slotted:
    __slots__ = ["x", "y"]    # no __dict__ — fixed attributes only
    def __init__(self, x, y):
        self.x = x
        self.y = y

import sys
n = Normal(1, 2)
s = Slotted(1, 2)
print(f"Normal:  {sys.getsizeof(n.__dict__)} bytes dict overhead")
print(f"Slotted: no __dict__")

# ============================================================
# FINAL TASK — put it all together:
#   Create a dataclass `Student` with:
#     name: str, grades: list[int] (default empty)
#   Add a method `average() -> float | None` (None if no grades)
#   Add a decorator `validate_grade` that raises ValueError
#     if a grade is not between 0-100
#   Write a generator that yields only students with average > 75
#   from a list of students
# ============================================================
