# ============================================================
# STAGE 1 — Variables & Types
# ============================================================

name = "Alice"
age = 30
height = 5.6
is_dev = True
nothing = None

print(type(name))
print(type(age))
print(type(is_dev))

# Type conversion
age_str = str(age)
pi = float("3.14")
num = int("42")

print(age_str, type(age_str))
print(pi, type(pi))
print(num, type(num))

# Multiple assignment
x = y = z = 0
a, b, c = 1, 2, 3
print(a, b, c)

MAX_SIZE = 100

print(f"Name: {name}, Age: {age}, Dev: {is_dev}")
print(f"In 5 years: {age + 5}")
