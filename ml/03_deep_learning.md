# Deep Learning — Interview Level

---

## 1. Neural Network Fundamentals

### Forward Pass
```
z[l] = W[l] · a[l-1] + b[l]
a[l] = activation(z[l])
```

### Backpropagation
Chain rule applied backward through layers:
```
∂L/∂W[l] = ∂L/∂a[l] · ∂a[l]/∂z[l] · ∂z[l]/∂W[l]
         = δ[l] · a[l-1]ᵀ

δ[l] = (W[l+1]ᵀ · δ[l+1]) ⊙ σ'(z[l])
```

**Key insight**: errors propagate backward weighted by the next layer's weights.

### Universal Approximation Theorem
A neural network with one hidden layer and enough neurons can approximate any continuous function. More layers = more efficient (depth buys expressiveness exponentially).

---

## 2. Activation Functions

| Function | Formula | Range | Use | Problem |
|----------|---------|-------|-----|---------|
| Sigmoid | 1/(1+e^-x) | (0,1) | Binary output | Vanishing gradient, not zero-centered |
| Tanh | (e^x-e^-x)/(e^x+e^-x) | (-1,1) | Hidden layers | Vanishing gradient |
| ReLU | max(0,x) | [0,∞) | Default hidden | Dying ReLU |
| Leaky ReLU | max(0.01x, x) | (-∞,∞) | When ReLU dies | Slight negative slope |
| GELU | x·Φ(x) | (-∞,∞) | Transformers | More complex |
| Softmax | e^xᵢ/Σe^xⱼ | (0,1), sum=1 | Multi-class output | Numerically unstable (use log-softmax) |

### Why ReLU works better than sigmoid
- No vanishing gradient for positive inputs
- Sparse activation (many neurons output 0) → more efficient
- Computationally simple

### Dying ReLU problem
Neurons stuck at 0 because gradient is 0 for negative inputs. Fix: Leaky ReLU, ELU, or careful initialization.

---

## 3. Optimization Algorithms

### Gradient Descent variants
- **Batch GD**: use all data → stable but slow
- **SGD**: use 1 sample → noisy but fast, can escape local minima
- **Mini-batch GD**: use N samples → balance of both (standard in practice)

### Optimizers

**SGD with Momentum**
```
v = β·v - α·∇L
θ = θ + v
```
Accumulates velocity in consistent gradient directions, dampens oscillation.

**Adam (most common in practice)**
```
m = β₁·m + (1-β₁)·∇L        # first moment (momentum)
v = β₂·v + (1-β₂)·∇L²       # second moment (variance)
m̂ = m/(1-β₁ᵗ)               # bias correction
v̂ = v/(1-β₂ᵗ)
θ = θ - α·m̂/(√v̂ + ε)
```
- Default: β₁=0.9, β₂=0.999, ε=1e-8
- Adaptive learning rate per parameter
- Fast convergence, good defaults

**AdamW**: Adam + decoupled weight decay (fixes L2 regularization bug in Adam)

### Learning Rate Scheduling
- **Cosine annealing**: smoothly reduces LR over training
- **Warmup**: start with small LR, increase, then decay (used in transformers)
- **ReduceLROnPlateau**: reduce when metric stops improving

---

## 4. Regularization Techniques

### Dropout
- During training: randomly zero out neurons with probability p
- During inference: scale outputs by (1-p), no dropout
- **Why it works**: ensemble of 2^N subnetworks, prevents co-adaptation
- Typical: p=0.5 for hidden layers, p=0.1-0.2 for input

### Batch Normalization
```
x̂ = (x - μ_batch) / √(σ²_batch + ε)
y = γ·x̂ + β    # learnable scale and shift
```
- Normalizes within each mini-batch
- Reduces internal covariate shift
- Allows higher learning rates
- Acts as regularizer (slightly)
- **Problem**: doesn't work well with small batches or RNNs

### Layer Normalization
- Normalizes across features within each sample (not across batch)
- Works for any batch size
- Standard in transformers

### Weight Decay (L2)
Adds λ||θ||² to loss → penalizes large weights → simpler models

### Early Stopping
Stop training when validation loss stops improving. Simple and effective.

---

## 5. Weight Initialization

### Why it matters
Bad initialization → vanishing/exploding gradients → training fails

### Xavier/Glorot initialization
```
W ~ Uniform(-√(6/(nᵢₙ+nₒᵤₜ)), √(6/(nᵢₙ+nₒᵤₜ)))
```
Designed for tanh/sigmoid — keeps variance constant across layers.

### He initialization
```
W ~ N(0, √(2/nᵢₙ))
```
Designed for ReLU — accounts for the half that's zeroed out.

### Rule of thumb
- Using ReLU → He init
- Using tanh/sigmoid → Xavier init
- Transformers → often custom init (e.g., 1/√d)

---

## 6. Vanishing & Exploding Gradients

### Vanishing Gradients
- Gradients shrink as they propagate backward → early layers don't learn
- Caused by: deep networks + sigmoid/tanh activation
- Fix: ReLU, residual connections, batch norm, LSTM gates

### Exploding Gradients
- Gradients grow exponentially → NaN weights
- Fix: **gradient clipping** (`clip_grad_norm_` in PyTorch)

### Gradient Clipping
```python
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

---

## 7. Convolutional Neural Networks (CNN)

### Convolution Operation
```
output[i,j] = Σ filter[m,n] × input[i+m, j+n]
```

### Key concepts
- **Filter/Kernel**: learnable weights that detect a pattern
- **Feature map**: output of applying filter to input
- **Stride**: step size of filter (larger → smaller output)
- **Padding**: add zeros around input to control output size
  - Same padding: output size = input size
  - Valid padding: no padding, output shrinks

### Pooling
- **Max pooling**: take max in window → translation invariance
- **Average pooling**: take mean → smoother features
- Global Average Pooling (GAP): replaces FC layers, fewer parameters

### Output size formula
```
output_size = (input_size - kernel_size + 2*padding) / stride + 1
```

### Why CNNs work for images
- **Local connectivity**: nearby pixels are correlated
- **Weight sharing**: same filter applied everywhere → translational invariance
- **Hierarchy**: early layers detect edges, later layers detect objects

### Classic Architectures
| Model | Innovation |
|-------|-----------|
| AlexNet | ReLU, dropout, GPU |
| VGG | Deep + simple (3×3 filters) |
| ResNet | Skip connections (residual learning) |
| Inception | Multi-scale filters in parallel |
| EfficientNet | Compound scaling (width/depth/resolution) |

### Residual Connection (ResNet)
```
output = F(x) + x    # skip connection
```
Solves vanishing gradient in very deep networks — gradients can flow directly through skip connections.

---

## 8. Recurrent Neural Networks (RNN)

### How it works
```
hₜ = tanh(Wₕ·hₜ₋₁ + Wₓ·xₜ + b)
yₜ = Wᵧ·hₜ
```
Hidden state carries information across time steps.

### Problem: Vanishing gradient through time
Gradients through many time steps → vanish or explode

### LSTM (Long Short-Term Memory)
Three gates control information flow:
```
fₜ = σ(Wf·[hₜ₋₁, xₜ] + bf)     # forget gate
iₜ = σ(Wi·[hₜ₋₁, xₜ] + bi)     # input gate
oₜ = σ(Wo·[hₜ₋₁, xₜ] + bo)     # output gate

c̃ₜ = tanh(Wc·[hₜ₋₁, xₜ] + bc)  # candidate cell
cₜ = fₜ ⊙ cₜ₋₁ + iₜ ⊙ c̃ₜ      # cell state (long-term memory)
hₜ = oₜ ⊙ tanh(cₜ)              # hidden state (short-term memory)
```

### GRU (Gated Recurrent Unit)
Simpler than LSTM, 2 gates instead of 3:
- Update gate: how much to update hidden state
- Reset gate: how much of past to forget
- Fewer parameters, comparable performance to LSTM

---

## 9. Transfer Learning

### Concept
Use weights pretrained on large dataset (ImageNet, C4 corpus) as starting point.

### Strategies
1. **Feature extraction**: freeze all layers, train only classification head
2. **Fine-tuning (partial)**: unfreeze last few layers, train with low LR
3. **Full fine-tuning**: unfreeze all layers, use very low LR throughout
4. **LoRA**: inject small trainable matrices, freeze base model (LLMs)

### When to fine-tune how much
- Small dataset + similar domain → freeze most, train head
- Small dataset + different domain → freeze fewer layers
- Large dataset → fine-tune more or fully

---

## Interview Quick-Fire

**Q: Why does deeper network not always perform better?**
Degradation problem: harder to optimize deep networks (vanishing gradients). ResNets solve this with skip connections.

**Q: What is the difference between batch size and learning rate?**
Large batch size → more stable gradient estimates → can use larger LR. Small batch → noisy gradients → need small LR. Rule: if you 8× batch size, try 8× LR (linear scaling rule).

**Q: What's the difference between parameters and hyperparameters?**
Parameters are learned during training (weights, biases). Hyperparameters are set before training (learning rate, batch size, architecture choices).

**Q: Explain the difference between model capacity and generalization.**
Capacity = model's ability to fit complex functions (more parameters = more capacity). Generalization = performance on unseen data. High capacity without regularization → overfitting.
