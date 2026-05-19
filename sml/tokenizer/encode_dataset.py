import sys
import numpy as np
sys.path.append('.')
from tokenizer import CharTokenizer

# Load raw text
with open("data/train.txt", "r", encoding="utf-8") as f:
    train_text = f.read()

with open("data/val.txt", "r", encoding="utf-8") as f:
    val_text = f.read()

# Build and save tokenizer vocabulary
tokenizer = CharTokenizer(train_text)
tokenizer.save("tokenizer/vocab.json")

print(f"Vocabulary size  : {tokenizer.vocab_size}")

# Encode both splits
train_tokens = tokenizer.encode(train_text)

val_tokens   = tokenizer.encode(val_text)
print(f"Val text        : {len(val_text):,} characters")

print(f"Train tokens     : {len(train_tokens):,}")
print(f"Val tokens       : {len(val_tokens):,}")

# Save as numpy arrays for fast loading during training
np.save("data/train.npy", np.array(train_tokens, dtype=np.uint16))
np.save("data/val.npy",   np.array(val_tokens,   dtype=np.uint16))

print()
print("Saved data/train.npy and data/val.npy")

# Show a sample of what the encoded data looks like
print()
print("--- First 20 tokens ---")
print(train_tokens[:20])
print()
print("--- Decoded back ---")
print(repr(tokenizer.decode(train_tokens[:20])))