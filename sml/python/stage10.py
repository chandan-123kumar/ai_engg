# ============================================================
# STAGE 10 — File I/O & Context Managers
# ============================================================

# --- Writing a file ---
with open("test.txt", "w") as f:
    f.write("Hello, World!\n")
    f.write("Second line\n")

# --- Reading entire file ---
with open("test.txt", "r") as f:
    content = f.read()
    print(content)

# --- Reading line by line (memory efficient for large files) ---
with open("test.txt", "r") as f:
    for line in f:
        print(line.strip())

# --- Reading all lines into a list ---
with open("test.txt", "r") as f:
    lines = f.readlines()
    print(lines)   # ['Hello, World!\n', 'Second line\n']

# --- Appending to a file ---
with open("test.txt", "a") as f:
    f.write("Third line\n")

# --- File modes ---
# "r"  — read (default), error if file missing
# "w"  — write, creates file, OVERWRITES if exists
# "a"  — append, creates file if missing
# "x"  — create, error if file already exists
# "rb" — read binary (images, PDFs etc)
# "wb" — write binary

# --- Why `with` (context manager)? ---
# Always use `with` — it guarantees file.close() even if an exception occurs
# Bad:
f = open("test.txt", "r")
data = f.read()
f.close()           # won't run if read() raises an exception

# Good:
with open("test.txt", "r") as f:
    data = f.read()  # file closed automatically on exit, even on error

# --- Working with paths (use pathlib, not os.path) ---
from pathlib import Path

p = Path("test.txt")
print(p.exists())       # True
print(p.suffix)         # .txt
print(p.stem)           # test
print(p.stat().st_size) # file size in bytes

# Write/read with pathlib directly
p.write_text("Written via pathlib\n")
print(p.read_text())

# Build paths safely (works on Windows & Mac/Linux)
home = Path.home()
config = home / ".config" / "app" / "settings.json"
print(config)

# --- Custom Context Manager ---
class Timer:
    import time

    def __enter__(self):
        import time
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.elapsed = time.time() - self.start
        print(f"Elapsed: {self.elapsed:.4f}s")
        return False    # don't suppress exceptions

with Timer():
    total = sum(x**2 for x in range(1000000))

# --- JSON (most common file format in real projects) ---
import json

data = {"name": "Alice", "age": 30, "skills": ["Python", "SQL"]}

# write JSON
with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

# read JSON
with open("data.json", "r") as f:
    loaded = json.load(f)

print(loaded)
print(loaded["skills"])

# ============================================================
# TASK:
#   1. Write a list of 5 dicts (name, score) to "scores.json"
#   2. Read it back
#   3. Print only names where score > 80, sorted by score descending
# ============================================================


dit = [{"name": "chandan2", "score": 12},{"name": "chandan1", "score": 12},{"name": "chandan", "score": 12}, {"name": "rohan", "score": 82}, {"name": "rohan1", "score": 81}]

with open("score.json", "w") as f:
    json.dump(dit, f, indent=2)
with open("score.json","r") as f:
    data = json.load(f)
    names = sorted(filter(lambda x: x["score"] > 80, data ), key=lambda x: x["score"], reverse=True)
    for name in names:
        print(name["name"], name["score"])