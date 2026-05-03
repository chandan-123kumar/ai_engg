import sys
sys.path.append('.')
from tokenizer import CharTokenizer

# Build tokenizer from training text
with open("data/train.txt", "r", encoding="utf-8") as f:
    text = f.read()

tokenizer = CharTokenizer(text)

print(f"Vocabulary size  : {tokenizer.vocab_size}")
print(f"All characters   : {repr(''.join(tokenizer.chars))}")
print()

# Test encoding
sample = "Hello World!"
# Only test with characters that exist in our vocabulary
sample = "To be, or not to be."
encoded = tokenizer.encode(sample)
print(f"Original text    : {sample}")
print(f"Encoded tokens   : {encoded}")
print()

# Test decoding
decoded = tokenizer.decode(encoded)
print(f"Decoded text     : {decoded}")
print()

# Verify round-trip is perfect
assert sample == decoded, "Round-trip failed!"
print("Round-trip check : PASSED ✅")