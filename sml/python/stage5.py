# ============================================================
# STAGE 5 — Control Flow (if / elif / else)
# ============================================================

# --- Basic if/elif/else ---
age = 20

if age < 13:
    print("child")
elif age < 18:
    print("teenager")
elif age < 60:
    print("adult")
else:
    print("senior")

# --- Ternary (one-liner if/else) ---
status = "even" if age % 2 == 0 else "odd"
print(status)

# --- Truthy / Falsy — critical to understand ---
# These all evaluate as False:
falsy = [0, 0.0, "", [], {}, set(), None, False]
for val in falsy:
    if not val:
        print(f"{repr(val)} is falsy")

# Everything else is truthy — very Pythonic to use directly:
name = "Alice"
if name:                    # instead of: if name != ""
    print(f"Hello {name}")

items = [1, 2, 3]
if items:                   # instead of: if len(items) > 0
    print("list has items")

# --- Nested if ---
score = 85
if score >= 60:
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    else:
        grade = "C"
else:
    grade = "F"
print(grade)

# --- match/case (Python 3.10+ — like switch) ---
command = "quit"

match command:
    case "start":
        print("Starting...")
    case "stop" | "quit":   # OR with |
        print("Stopping...")
    case _:                 # default
        print("Unknown command")

# ============================================================
# TASK:
#   Write a function-free script that:
#   1. Sets a variable `temp` (temperature in celsius)
#   2. Prints "freezing" if < 0
#      "cold" if 0–15
#      "warm" if 16–30
#      "hot" if > 30
#   3. Also prints "boiling!" if temp >= 100
#      (hint: this should work alongside the above, not replace it)
# ============================================================
temp = 25
if temp < 0:
    print("freezing")
elif temp<= 15:
    print("cold")
elif temp <= 30:
    print("warm")
elif temp >= 100:
     print("boiling!")    
else:
    print("hot")