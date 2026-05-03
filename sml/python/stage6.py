# ============================================================
# STAGE 6 — Loops (for, while, comprehensions)
# ============================================================

# --- for loop ---
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# --- range ---
for i in range(5):        # 0,1,2,3,4
    print(i)
print()

for i in range(2, 10, 2): # 2,4,6,8
    print(i, end=" ")
print()

# --- enumerate — index + value ---
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")

# --- zip — loop two lists together ---
names = ["Alice", "Bob", "Carol"]
scores = [95, 82, 78]
for name, score in zip(names, scores):
    print(f"{name}: {score}")

# --- while loop ---
count = 0
while count < 5:
    print(count, end=" ")
    count += 1
print()

# --- break, continue, else ---
for n in range(10):
    if n == 3:
        continue        # skip 3
    if n == 7:
        break           # stop at 7
    print(n, end=" ")
print()

# loop else — runs only if loop wasn't broken
for n in range(5):
    if n == 10:
        break
else:
    print("loop completed without break")

# --- List Comprehension — most Pythonic pattern ---
squares = [x**2 for x in range(10)]
print(squares)

evens = [x for x in range(20) if x % 2 == 0]
print(evens)

# with transformation
words = ["hello", "world", "python"]
upper = [w.upper() for w in words]
print(upper)

# --- Dict Comprehension ---
sq_dict = {x: x**2 for x in range(6)}
print(sq_dict)

# --- Set Comprehension ---
unique_lens = {len(w) for w in words}
print(unique_lens)

# --- Generator Expression (lazy — doesn't build list in memory) ---
total = sum(x**2 for x in range(10) if x%2 == 0)  # no list created
print(total)

# ============================================================
# TASK:
#   Using a single list comprehension, create a list of
#   all numbers from 1–50 that are divisible by 3 but not by 9
#   Expected: [3, 6, 12, 15, 21, 24, 30, 33, 39, 42, 48]
# ============================================================
[x for x in range(1, 51) if x%3 == 0 and x%9 !=0]
