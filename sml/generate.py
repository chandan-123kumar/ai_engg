import torch
import sys
sys.path.append('.')

from model.model import GPT
from tokenizer.tokenizer import CharTokenizer

# ─────────────────────────────────────────────
# LOAD CHECKPOINT
# ─────────────────────────────────────────────

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Device     : {device}")

checkpoint = torch.load(
    "checkpoints/best_model.pt",
    map_location=device,
    weights_only=True
)

# Rebuild model from saved config
config = checkpoint['config']
print(f"Checkpoint : step {checkpoint['step']}, val loss {checkpoint['val_loss']:.4f}")
print()

model = GPT(**config).to(device)
model.load_state_dict(checkpoint['model_state'])
model.eval()

# Load tokenizer
tokenizer = CharTokenizer.load("tokenizer/vocab.json")

# ─────────────────────────────────────────────
# GENERATION FUNCTION
# ─────────────────────────────────────────────

@torch.no_grad()
def generate(prompt, max_new_tokens=300, temperature=1.0, top_k=10):
    # Encode the prompt into token IDs
    tokens = tokenizer.encode(prompt)
    idx    = torch.tensor(tokens, dtype=torch.long, device=device).unsqueeze(0)

    for _ in range(max_new_tokens):
        # Crop to block_size if sequence gets too long
        idx_cond = idx[:, -config['block_size']:]

        # Forward pass — get scores for next token
        logits, _ = model(idx_cond)
        logits     = logits[:, -1, :]  # take last position only

        # Apply temperature — scale the scores
        logits = logits / temperature

        # Apply top-k — zero out everything outside top k
        if top_k is not None:
            values, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < values[:, -1:]] = float('-inf')

        # Convert scores to probabilities
        probs = torch.softmax(logits, dim=-1)

        # Sample one token from the distribution
        next_token = torch.multinomial(probs, num_samples=1)

        # Append to sequence and repeat
        idx = torch.cat([idx, next_token], dim=1)

    # Decode all tokens back to text
    return tokenizer.decode(idx[0].tolist())


# ─────────────────────────────────────────────
# GENERATE WITH DIFFERENT SETTINGS
# ─────────────────────────────────────────────

prompt = "list of shakepear books:\n"

print("=" * 50)
print(f"Prompt: {repr(prompt)}")
print("=" * 50)

# Conservative — low temperature
print("\n--- temperature=0.5, top_k=20 (conservative) ---\n")
print(generate(prompt, max_new_tokens=300, temperature=0.5, top_k=20))

# Balanced — default settings
print("\n--- temperature=1.0, top_k=40 (balanced) ---\n")
print(generate(prompt, max_new_tokens=300, temperature=1.0, top_k=40))

# Creative — high temperature
print("\n--- temperature=1.3, top_k=50 (creative) ---\n")
print(generate(prompt, max_new_tokens=300, temperature=1.3, top_k=50))