# SML — Small Language Model from Scratch

A minimal GPT-style language model built from scratch in PyTorch, trained on the TinyShakespeare dataset. The goal is to understand every part of a transformer — no magic black boxes.

## What's inside

```
sml/
├── data/
│   ├── download.py        # Download TinyShakespeare dataset
│   ├── prepare.py         # Split into train/val text files
│   ├── inspect.py         # Inspect dataset stats
│   ├── input.txt          # Raw dataset
│   ├── train.npy          # Encoded training tokens
│   └── val.npy            # Encoded validation tokens
├── tokenizer/
│   ├── tokenizer.py       # Character-level tokenizer
│   ├── encode_dataset.py  # Encode text files → .npy token arrays
│   ├── test_tokenizer.py  # Sanity-check encode/decode round-trip
│   └── vocab.json         # Saved vocabulary
├── model/
│   ├── model.py           # GPT model (Head, MultiHeadAttention, Block, GPT)
│   └── inspect_model.py   # Count parameters and test a forward pass
├── checkpoints/
│   └── best_model.pt      # Saved checkpoint (best validation loss)
├── check/
│   └── check.py           # Additional checks / debugging helpers
├── train.py               # Training loop with checkpointing
└── generate.py            # Load checkpoint and sample text
```

## Architecture

| Component | Details |
|---|---|
| Model type | Decoder-only Transformer (GPT-style) |
| Tokenizer | Character-level |
| Embedding dim | 128 |
| Attention heads | 4 |
| Transformer layers | 4 |
| Context length | 128 tokens |
| Dropout | 0.1 |
| Activation | GELU |

The model follows the standard pre-norm transformer: LayerNorm → Multi-Head Self-Attention → residual, then LayerNorm → FeedForward → residual.

## Quick start

### 1. Set up environment

**Using conda (recommended)**

```bash
conda create -n sml python=3.11
conda activate sml
conda install pytorch numpy -c pytorch
pip install requests
```

**Using pip + venv**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install torch numpy requests
```

### 2. Download and prepare data

```bash
python data/download.py        # downloads ~1MB TinyShakespeare text
python data/prepare.py         # splits into train.txt / val.txt (90/10)
python tokenizer/encode_dataset.py  # encodes text → train.npy / val.npy
```

### 3. Train

```bash
python train.py
```

Training runs for 5000 steps (~minutes on CPU, faster on MPS/GPU). Checkpoints are saved to `checkpoints/best_model.pt` whenever validation loss improves.

Example output:

```
Training on : mps
Vocab size  : 65
Train tokens: 1,003,854
Val tokens  : 111,540
Parameters  : 1,610,817

step     0 | train loss 4.1823 | val loss 4.1847 | time 0.3s
step   500 | train loss 2.1044 | val loss 2.1612 | time 14.2s
         ✅ checkpoint saved (val loss 2.1612)
...
```

### 4. Generate text

```bash
python generate.py
```

This loads the best checkpoint and samples text at three temperature settings (conservative, balanced, creative).

## Key hyperparameters

Edit the top of `train.py` to adjust:

| Parameter | Default | Description |
|---|---|---|
| `batch_size` | 32 | Sequences per training step |
| `block_size` | 128 | Context window length |
| `max_steps` | 5000 | Total training steps |
| `lr` | 3e-4 | Learning rate (AdamW) |
| `n_embd` | 128 | Embedding dimension |
| `n_heads` | 4 | Attention heads |
| `n_layers` | 4 | Transformer blocks |

## Inspect the model

```bash
python model/inspect_model.py
```

Prints a full layer-by-layer parameter count and runs a dummy forward pass to verify the model works before training.

## Dataset

[TinyShakespeare](https://github.com/karpathy/char-rnn/tree/master/data/tinyshakespeare) — ~1M characters of Shakespeare plays. Classic benchmark for character-level language models.

## Hardware

The training script auto-detects the best available device:

- **MPS** (Apple Silicon) — used if available
- **CPU** — fallback
