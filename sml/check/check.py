import torch
import numpy as np

print(f"PyTorch version : {torch.__version__}")
print(f"MPS available   : {torch.backends.mps.is_available()}")
print(f"NumPy version   : {np.__version__}")

# Quick tensor test on MPS
device = "mps" if torch.backends.mps.is_available() else "cpu"
x = torch.tensor([1.0, 2.0, 3.0]).to(device)
print(f"Tensor on {device}: {x}")