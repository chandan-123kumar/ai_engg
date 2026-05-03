import sys
import torch
sys.path.append('.')
from model import GPT

# Our hyperparameters
vocab_size  = 65
n_embd      = 128
n_heads     = 4
n_layers    = 4
block_size  = 128
dropout     = 0.1

model = GPT(
    vocab_size  = vocab_size,
    n_embd      = n_embd,
    n_heads     = n_heads,
    n_layers    = n_layers,
    block_size  = block_size,
    dropout     = dropout,
)

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
trainable    = sum(p.numel() for p in model.parameters() if p.requires_grad)

print(f"Total parameters    : {total_params:,}")
print(f"Trainable parameters: {trainable:,}")
print()

# Show each layer and its size
print("--- Layer breakdown ---")
for name, param in model.named_parameters():
    print(f"{name:45s} {str(list(param.shape)):20s} {param.numel():>10,}")

print()

# Test a forward pass with dummy data
device = "mps" if torch.backends.mps.is_available() else "cpu"
model  = model.to(device)

dummy_input   = torch.randint(0, vocab_size, (2, block_size)).to(device)
dummy_targets = torch.randint(0, vocab_size, (2, block_size)).to(device)

logits, loss = model(dummy_input, dummy_targets)

print(f"Input shape  : {list(dummy_input.shape)}")
print(f"Output shape : {list(logits.shape)}")
print(f"Loss         : {loss.item():.4f}")
print(f"Device       : {device}")
print()
print("Forward pass : PASSED ✅")