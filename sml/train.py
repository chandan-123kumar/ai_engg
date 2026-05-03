import torch
import numpy as np
import sys
import os
import time
sys.path.append('.')

from model.model import GPT
from tokenizer.tokenizer import CharTokenizer

# ─────────────────────────────────────────────
# HYPERPARAMETERS
# ─────────────────────────────────────────────
# These control the training process.
# Do not change these for your first run.

batch_size  = 32    # sequences per training step
block_size  = 128   # characters per sequence
max_steps   = 5000  # total training steps
eval_every  = 500   # evaluate val loss every N steps
eval_steps  = 50    # how many batches to use for evaluation
lr          = 3e-4  # learning rate

# Model hyperparameters — must match inspect_model.py
n_embd      = 128
n_heads     = 4
n_layers    = 4
dropout     = 0.1

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Training on : {device}")

# Load vocabulary
tokenizer  = CharTokenizer.load("tokenizer/vocab.json")
vocab_size = tokenizer.vocab_size
print(f"Vocab size  : {vocab_size}")

# Load encoded datasets
train_data = torch.tensor(
    np.load("data/train.npy").astype(np.int64)
)
val_data = torch.tensor(
    np.load("data/val.npy").astype(np.int64)
)

print(f"Train tokens: {len(train_data):,}")
print(f"Val tokens  : {len(val_data):,}")
print()

# ─────────────────────────────────────────────
# BATCH LOADER
# ─────────────────────────────────────────────
# Randomly samples a batch of sequences from
# the dataset. Each sequence is block_size long.
# Targets are the same sequences shifted by 1 —
# that's what the model learns to predict.

def get_batch(data):
    # Pick random starting positions
    ix = torch.randint(len(data) - block_size, (batch_size,))
    # Stack sequences into a batch
    x  = torch.stack([data[i   : i+block_size  ] for i in ix])
    y  = torch.stack([data[i+1 : i+block_size+1] for i in ix])
    return x.to(device), y.to(device)

# ─────────────────────────────────────────────
# LOSS EVALUATION
# ─────────────────────────────────────────────
# Runs the model on several batches without
# updating parameters. Gives an honest estimate
# of how well the model is doing.

@torch.no_grad()
def estimate_loss():
    model.eval()
    losses = {}
    for split, data in [("train", train_data), ("val", val_data)]:
        batch_losses = []
        for _ in range(eval_steps):
            x, y = get_batch(data)
            _, loss = model(x, y)
            batch_losses.append(loss.item())
        losses[split] = sum(batch_losses) / len(batch_losses)
    model.train()
    return losses

# ─────────────────────────────────────────────
# MODEL + OPTIMIZER
# ─────────────────────────────────────────────

model = GPT(
    vocab_size = vocab_size,
    n_embd     = n_embd,
    n_heads    = n_heads,
    n_layers   = n_layers,
    block_size = block_size,
    dropout    = dropout,
).to(device)

optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

total_params = sum(p.numel() for p in model.parameters())
print(f"Parameters  : {total_params:,}")
print(f"Max steps   : {max_steps:,}")
print()

# ─────────────────────────────────────────────
# TRAINING LOOP
# ─────────────────────────────────────────────

os.makedirs("checkpoints", exist_ok=True)
best_val_loss = float('inf')
start_time    = time.time()

for step in range(max_steps):

    # Evaluate periodically
    if step % eval_every == 0:
        losses = estimate_loss()
        elapsed = time.time() - start_time
        print(
            f"step {step:5d} | "
            f"train loss {losses['train']:.4f} | "
            f"val loss {losses['val']:.4f} | "
            f"time {elapsed:.1f}s"
        )

        # Save checkpoint if val loss improved
        if losses['val'] < best_val_loss:
            best_val_loss = losses['val']
            torch.save({
                'step'          : step,
                'model_state'   : model.state_dict(),
                'optimizer_state': optimizer.state_dict(),
                'val_loss'      : best_val_loss,
                'config': {
                    'vocab_size' : vocab_size,
                    'n_embd'     : n_embd,
                    'n_heads'    : n_heads,
                    'n_layers'   : n_layers,
                    'block_size' : block_size,
                    'dropout'    : dropout,
                }
            }, "checkpoints/best_model.pt")
            print(f"         ✅ checkpoint saved (val loss {best_val_loss:.4f})")

    # ── Core training step ──

    # 1. Get a random batch
    x, y = get_batch(train_data)

    # 2. Forward pass — compute predictions and loss
    logits, loss = model(x, y)

    # 3. Backward pass — compute gradients
    optimizer.zero_grad()
    loss.backward()

    # 4. Clip gradients — prevents explosively large updates
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

    # 5. Optimizer step — update parameters
    optimizer.step()

# ─────────────────────────────────────────────
# FINAL EVALUATION
# ─────────────────────────────────────────────

losses = estimate_loss()
total_time = time.time() - start_time
print()
print(f"Training complete in {total_time:.1f}s")
print(f"Final train loss : {losses['train']:.4f}")
print(f"Final val loss   : {losses['val']:.4f}")
print(f"Best val loss    : {best_val_loss:.4f}")
print(f"Checkpoint saved : checkpoints/best_model.pt")