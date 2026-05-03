import torch
import torch.nn as nn
from torch.nn import functional as F


# ─────────────────────────────────────────────
# 1. SINGLE ATTENTION HEAD
# ─────────────────────────────────────────────
# Each head learns a different way of relating
# tokens to each other. Think of it as one
# "perspective" on the sequence.
#
# For each token it computes:
#   Query  — "what am I looking for?"
#   Key    — "what do I contain?"
#   Value  — "what do I send if attended to?"
#
# Attention score = how well Query matches Key
# Output = weighted sum of Values
# ─────────────────────────────────────────────

class Head(nn.Module):
    def __init__(self, head_size, n_embd, block_size, dropout):
        super().__init__()
        self.key   = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.dropout = nn.Dropout(dropout)

        # Causal mask — token at position i can only
        # attend to positions 0..i, never the future.
        # This is what makes it a language model and
        # not a bidirectional encoder like BERT.
        self.register_buffer(
            'tril',
            torch.tril(torch.ones(block_size, block_size))
        )

    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x)    # (B, T, head_size)
        q = self.query(x)  # (B, T, head_size)

        # Attention scores — scale by sqrt(head_size)
        # to prevent values getting too large before softmax
        wei = q @ k.transpose(-2, -1) * C**-0.5  # (B, T, T)

        # Mask out future positions with -inf
        # so softmax gives them zero weight
        wei = wei.masked_fill(
            self.tril[:T, :T] == 0, float('-inf')
        )
        wei = F.softmax(wei, dim=-1)
        wei = self.dropout(wei)

        # Weighted sum of values
        v = self.value(x)  # (B, T, head_size)
        return wei @ v     # (B, T, head_size)


# ─────────────────────────────────────────────
# 2. MULTI-HEAD ATTENTION
# ─────────────────────────────────────────────
# Run several attention heads in parallel, each
# learning different relationships between tokens.
# Then concatenate and project back to n_embd.
#
# Example: one head might learn subject-verb
# agreement, another learns pronoun references.
# ─────────────────────────────────────────────

class MultiHeadAttention(nn.Module):
    def __init__(self, n_heads, head_size, n_embd, block_size, dropout):
        super().__init__()
        self.heads = nn.ModuleList([
            Head(head_size, n_embd, block_size, dropout)
            for _ in range(n_heads)
        ])
        # Project concatenated heads back to n_embd
        self.proj    = nn.Linear(n_embd, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # Run all heads, concatenate along last dim
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return self.dropout(self.proj(out))


# ─────────────────────────────────────────────
# 3. FEEDFORWARD NETWORK
# ─────────────────────────────────────────────
# After attention lets tokens communicate,
# this layer lets each token "think" on its own.
# It's a simple 2-layer MLP applied independently
# to each token position.
#
# The inner layer is 4x wider than n_embd —
# this is a standard transformer convention.
# ─────────────────────────────────────────────

class FeedForward(nn.Module):
    def __init__(self, n_embd, dropout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),  # expand
            nn.GELU(),                        # smooth activation
            nn.Linear(4 * n_embd, n_embd),  # contract
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


# ─────────────────────────────────────────────
# 4. TRANSFORMER BLOCK
# ─────────────────────────────────────────────
# One full layer of the transformer.
# Combines attention + feedforward with:
#
# - Residual connections (x + ...) so gradients
#   flow easily during backprop
# - LayerNorm before each sub-layer to keep
#   activations stable (this is "pre-norm",
#   slightly different from the original paper)
# ─────────────────────────────────────────────

class Block(nn.Module):
    def __init__(self, n_embd, n_heads, block_size, dropout):
        super().__init__()
        head_size = n_embd // n_heads
        self.sa   = MultiHeadAttention(
            n_heads, head_size, n_embd, block_size, dropout
        )
        self.ffwd = FeedForward(n_embd, dropout)
        self.ln1  = nn.LayerNorm(n_embd)
        self.ln2  = nn.LayerNorm(n_embd)

    def forward(self, x):
        # Attention — tokens communicate
        x = x + self.sa(self.ln1(x))
        # Feedforward — tokens think individually
        x = x + self.ffwd(self.ln2(x))
        return x


# ─────────────────────────────────────────────
# 5. FULL GPT MODEL
# ─────────────────────────────────────────────
# Puts everything together:
#
# Token embedding  — ID → vector
# Position embedding — where in sequence am I?
# N transformer blocks — attention + feedforward
# Final LayerNorm — stabilize before output
# Output head — vector → vocabulary scores
# ─────────────────────────────────────────────

class GPT(nn.Module):
    def __init__(self, vocab_size, n_embd=128, n_heads=4,
                 n_layers=4, block_size=128, dropout=0.1):
        super().__init__()
        self.block_size = block_size

        self.tok_emb = nn.Embedding(vocab_size, n_embd)
        self.pos_emb = nn.Embedding(block_size, n_embd)

        self.blocks = nn.Sequential(*[
            Block(n_embd, n_heads, block_size, dropout)
            for _ in range(n_layers)
        ])

        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size, bias=False)

    def forward(self, idx, targets=None):
        B, T = idx.shape

        # Token + position embeddings added together
        tok = self.tok_emb(idx)                              # (B, T, n_embd)
        pos = self.pos_emb(torch.arange(T, device=idx.device))  # (T, n_embd)
        x = tok + pos                                        # (B, T, n_embd)

        # Pass through all transformer blocks
        x = self.blocks(x)
        x = self.ln_f(x)

        # Project to vocabulary size — one score per token
        logits = self.head(x)                               # (B, T, vocab_size)

        # If targets provided, compute cross-entropy loss
        loss = None
        if targets is not None:
            B, T, C = logits.shape
            loss = F.cross_entropy(
                logits.view(B * T, C),
                targets.view(B * T)
            )

        return logits, loss