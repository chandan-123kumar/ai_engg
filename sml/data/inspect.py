with open("data/input.txt", "r", encoding="utf-8") as f:
    text = f.read()

print(f"Total characters : {len(text):,}")
print(f"Total lines      : {text.count(chr(10)):,}")
print(f"Unique characters: {len(set(text))}")
print()
print("--- First 500 characters ---")
print(text[:500])
print()
print("--- All unique characters ---")
chars = sorted(set(text))
print(repr(''.join(chars)))