# ============================================================
# STAGE 3 — Strings
# ============================================================

# --- Creation ---
s1 = 'single quotes'
s2 = "double quotes"
s3 = """multiline
string spans
multiple lines"""

print(s3)

# --- Indexing & Slicing ---
s = "Python"
print(s[0])     # P      (first)
print(s[-1])    # n      (last)
print(s[1:4])   # yth    (index 1 up to, not including, 4)
print(s[:3])    # Pyt    (start to 3)
print(s[3:])    # hon    (3 to end)
print(s[::-1])  # nohtyP (reverse)

# --- Common Methods ---
text = "  Hello, World!  "
print(text.strip())         # remove whitespace from both ends
print(text.lower())         # hello, world!
print(text.upper())         # HELLO, WORLD!
print(text.replace("World", "Python"))
print(text.strip().split(", "))  # ['Hello', 'World!']

sentence = "the quick brown fox"
print(sentence.title())     # The Quick Brown Fox
print(sentence.count("o"))  # 2
print(sentence.find("quick"))  # 4 (index) or -1 if not found
print(sentence.startswith("the"))  # True
print(sentence.endswith("fox"))    # True

# --- f-strings (best way to format) ---
name = "Alice"
score = 95.678
print(f"Name: {name}")
print(f"Score: {score:.2f}")    # 2 decimal places → 95.68
print(f"Score: {score:>10.2f}") # right-aligned in 10 chars

# --- Joining & Splitting ---
words = ["Python", "is", "awesome"]
print(" ".join(words))          # Python is awesome
print("-".join(words))          # Python-is-awesome

csv = "a,b,c,d"
print(csv.split(","))           # ['a', 'b', 'c', 'd']

# --- Immutability ---
s = "hello"
# s[0] = "H"  ← TypeError! Strings are immutable
s = "H" + s[1:]  # must create a new string
print(s)          # Hello

# --- Check content ---
print("abc123".isalnum())   # True
print("123".isdigit())      # True
print("abc".isalpha())      # True
print("  ".isspace())       # True

# ============================================================
# TASK:
#   s = "  Data Science 2024  "
#   1. Strip whitespace
#   2. Convert to lowercase
#   3. Replace "2024" with "2025"
#   4. Split into a list of words
#   5. Print each word on a new line using join with "\n"
# ============================================================
