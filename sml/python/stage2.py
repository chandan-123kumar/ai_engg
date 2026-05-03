# ============================================================
# STAGE 2 — Operators & Comparisons
# ============================================================

# --- Arithmetic ---
print(10 + 3)   # 13
print(10 - 3)   # 7
print(10 * 3)   # 30
print(10 / 3)   # 3.333... (always float)
print(10 // 3)  # 3        (floor division)
print(10 % 3)   # 1        (modulo / remainder)
print(10 ** 3)  # 1000     (power)

# --- Comparison (return bool) ---
print(10 > 3)   # True
print(10 < 3)   # False
print(10 == 10) # True
print(10 != 3)  # True
print(10 >= 10) # True

# --- Logical ---
print(True and False)  # False
print(True or False)   # True
print(not True)        # False

# Chained comparisons (Pythonic!)
age = 25
print(18 <= age <= 65)  # True

# --- Identity vs Equality ---
a = [1, 2, 3]
b = [1, 2, 3]
c = a

print(a == b)   # True  — same VALUES
print(a is b)   # False — different OBJECTS in memory
print(a is c)   # True  — same OBJECT (c points to a)

# --- Membership ---
fruits = ["apple", "banana", "cherry"]
print("banana" in fruits)
print("grape" not in fruits)

# --- Augmented assignment ---
x = 10
x += 5
x -= 3
x *= 2
x //= 5
print(x)
