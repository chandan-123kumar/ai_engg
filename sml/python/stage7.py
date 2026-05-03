# ============================================================
# STAGE 7 — Functions & Lambdas
# ============================================================

# --- Basic function ---
def greet(name):
    return f"Hello, {name}!"

print(greet("Alice"))

# --- Default arguments ---
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

print(greet("Alice"))
print(greet("Bob", "Hi"))

# --- Keyword arguments ---
print(greet(greeting="Hey", name="Carol"))

# --- *args — variable positional arguments (tuple) ---
def total(*nums):
    print(type(nums), nums)   # <class 'tuple'>
    return sum(nums)

print(total(1, 2, 3))
print(total(1, 2, 3, 4, 5))

# --- **kwargs — variable keyword arguments (dict) ---
def show_info(**details):
    print(type(details), details)  # <class 'dict'>
    for key, val in details.items():
        print(f"  {key}: {val}")

show_info(name="Alice", age=30, city="NYC")

# --- Combining all parameter types ---
# order must be: positional, *args, keyword, **kwargs
def mixed(a, b, *args, flag=False, **kwargs):
    print(a, b, args, flag, kwargs)

mixed(1, 2, 3, 4, flag=True, x=10, y=20)

# --- Return multiple values (actually a tuple) ---
def min_max(nums):
    return min(nums), max(nums)   # returns tuple

lo, hi = min_max([3, 1, 4, 1, 5, 9])
print(lo, hi)

# --- Lambda — anonymous one-liner function ---
square = lambda x: x**2
print(square(5))

add = lambda x, y: x + y
print(add(3, 4))

# Lambdas shine with sorted/map/filter
names = ["Charlie", "Alice", "Bob"]
print(sorted(names, key=lambda n: len(n)))   # sort by length

pairs = [(1, 3), (2, 1), (4, 2)]
print(sorted(pairs, key=lambda p: p[1]))     # sort by second element

nums = [1, 2, 3, 4, 5, 6]
evens = list(filter(lambda x: x % 2 == 0, nums))
doubled = list(map(lambda x: x * 2, nums))
print(evens)
print(doubled)

# --- Scope: LEGB rule ---
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)    # local
    inner()
    print(x)        # enclosing

outer()
print(x)            # global

# --- First-class functions (functions are objects) ---
def apply(func, value):
    return func(value)

print(apply(square, 9))         # 81
print(apply(str.upper, "hi"))   # HI

# ============================================================
# TASK:
#   1. Write a function `summarize(*nums)` that returns a dict:
#      {"count": n, "sum": s, "mean": m, "min": lo, "max": hi}
#   2. Sort this list by the absolute value using a lambda:
#      nums = [-10, 3, -1, 7, -5]
#      Expected: [-1, 3, -5, 7, -10]
# ============================================================
