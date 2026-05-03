# ============================================================
# STAGE 9 — Error Handling
# ============================================================

# --- Basic try/except ---
try:
    x = 1 / 0
except ZeroDivisionError:
    print("can't divide by zero")

# --- Catching multiple exceptions ---
def parse(val):
    try:
        return int(val)
    except ValueError:
        print(f"can't convert {val!r} to int")
    except TypeError:
        print(f"wrong type: {type(val)}")

parse("abc")
parse(None)
parse("42")    # works fine

# --- except with the exception object ---
try:
    int("bad")
except ValueError as e:
    print(f"Error: {e}")
    print(type(e))

# --- else — runs only if no exception was raised ---
try:
    result = 10 / 2
except ZeroDivisionError:
    print("error")
else:
    print(f"success: {result}")   # runs here

# --- finally — always runs (cleanup) ---
try:
    f = open("nonexistent.txt")
except FileNotFoundError as e:
    print(f"File error: {e}")
finally:
    print("this always runs — use for cleanup")

# --- Raising exceptions ---
def set_age(age):
    if not isinstance(age, int):
        raise TypeError(f"age must be int, got {type(age).__name__}")
    if age < 0 or age > 150:
        raise ValueError(f"age {age} out of range")
    return age

try:
    set_age(-5)
except ValueError as e:
    print(e)

try:
    set_age("old")
except TypeError as e:
    print(e)

# --- Custom exceptions ---
class InsufficientFundsError(Exception):
    def __init__(self, amount, balance):
        self.amount = amount
        self.balance = balance
        super().__init__(f"tried to withdraw {amount}, only {balance} available")

def withdraw(balance, amount):
    if amount > balance:
        raise InsufficientFundsError(amount, balance)
    return balance - amount

try:
    withdraw(100, 250)
except InsufficientFundsError as e:
    print(e)
    print(f"short by: {e.amount - e.balance}")

# --- Common built-in exceptions ---
# ValueError      — right type, wrong value:  int("abc")
# TypeError       — wrong type:               "a" + 1
# KeyError        — dict key missing:         d["x"]
# IndexError      — list index out of range:  lst[99]
# AttributeError  — object has no attribute:  None.upper()
# FileNotFoundError — file doesn't exist
# ZeroDivisionError — divide by zero

# ============================================================
# TASK:
#   Write a function `safe_divide(a, b)` that:
#   1. Raises TypeError if either argument is not a number
#   2. Raises ValueError if b is 0
#   3. Returns the result otherwise
#   Test all 3 cases using try/except
# ============================================================
