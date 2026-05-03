# Python — Beginner to Advanced

A 12-stage hands-on crash course. Each stage is a standalone file with concepts, examples, and a task at the bottom.

## Stages

| File | Topic | Key Concepts |
|------|-------|--------------|
| [stage1.py](stage1.py) | Variables & Types | int, float, str, bool, None, type conversion, f-strings |
| [stage2.py](stage2.py) | Operators & Comparisons | arithmetic, logical, identity (`is`), membership (`in`) |
| [stage3.py](stage3.py) | Strings | slicing, methods, f-strings, immutability |
| [stage4.py](stage4.py) | Data Structures | list, tuple, set, dict — when to use each |
| [stage5.py](stage5.py) | Control Flow | if/elif/else, ternary, truthy/falsy, match/case |
| [stage6.py](stage6.py) | Loops | for, while, enumerate, zip, comprehensions, generators |
| [stage7.py](stage7.py) | Functions & Lambdas | args, *args, **kwargs, scope (LEGB), first-class functions |
| [stage8.py](stage8.py) | Classes & OOP | inheritance, super(), @property, @classmethod, dunders |
| [stage9.py](stage9.py) | Error Handling | try/except/else/finally, raising, custom exceptions |
| [stage10.py](stage10.py) | File I/O | open modes, context managers, pathlib, json |
| [stage11.py](stage11.py) | Modules, Decorators, Generators | functools, Counter, defaultdict, yield, send() |
| [stage12.py](stage12.py) | Advanced | type hints, dataclasses, itertools, walrus operator, \_\_slots\_\_ |

## How to run

```bash
python stage1.py
```

## Quick Reference

```python
# Comprehensions
[x**2 for x in range(10) if x % 2 == 0]
{k: v for k, v in pairs}

# Unpacking
a, *rest = [1, 2, 3, 4]        # a=1, rest=[2,3,4]
first, *_, last = [1,2,3,4,5]  # first=1, last=5

# Useful builtins
zip(a, b)           # pair two iterables
enumerate(a)        # (index, value) pairs
map(fn, iterable)   # apply fn to each
filter(fn, iterable)# keep where fn is True
sorted(a, key=fn, reverse=True)
any(x > 0 for x in nums)
all(x > 0 for x in nums)

# String
" ".join(words)
s.split(",")
s.strip().lower()

# Dict
d.get("key", default)
d.items(), d.keys(), d.values()

# Collections
from collections import Counter, defaultdict, deque

# Pathlib
from pathlib import Path
Path("file.txt").read_text()
Path("file.txt").write_text("...")
```
