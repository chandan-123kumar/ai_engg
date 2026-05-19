# Math Foundations for ML Interviews

---

## 1. Linear Algebra

### Vectors & Matrices
- Vector: ordered list of numbers → represents a data point or weights
- Matrix multiplication: `(m×k) @ (k×n) = (m×n)` — rows of A dot with cols of B
- **Why it matters**: neural network forward pass is just matrix multiplication

### Eigenvalues & Eigenvectors
```
A·v = λ·v
```
- `v` = eigenvector (direction unchanged by transformation)
- `λ` = eigenvalue (how much it stretches)
- **Interview use**: PCA finds eigenvectors of covariance matrix

### SVD (Singular Value Decomposition)
```
A = U · Σ · Vᵀ
```
- U: left singular vectors (output space)
- Σ: diagonal matrix of singular values (importance)
- Vᵀ: right singular vectors (input space)
- **Interview use**: dimensionality reduction, recommender systems (matrix factorization)

### Norms
- L1 norm: `||x||₁ = Σ|xᵢ|` → sparse solutions (Lasso)
- L2 norm: `||x||₂ = √(Σxᵢ²)` → smooth solutions (Ridge)
- **Trick question**: "Why does L1 produce sparsity?" — L1 has corners at axes; gradient descent hits zero exactly

---

## 2. Calculus

### Derivatives & Chain Rule
```python
# Chain rule: d/dx f(g(x)) = f'(g(x)) · g'(x)
# This IS backpropagation
```

### Gradient
- Vector of partial derivatives: `∇f = [∂f/∂x₁, ∂f/∂x₂, ...]`
- Points in direction of steepest ascent
- Gradient descent: `θ = θ - α·∇L(θ)`

### Key Derivatives to Know
| Function | Derivative |
|----------|-----------|
| sigmoid σ(x) | σ(x)(1 - σ(x)) |
| tanh(x) | 1 - tanh²(x) |
| ReLU | 0 if x<0, 1 if x>0 |
| log(x) | 1/x |
| softmax | σᵢ(δᵢⱼ - σⱼ) |

### Jacobian & Hessian
- Jacobian: matrix of all partial derivatives (for vector functions)
- Hessian: matrix of second derivatives (curvature of loss landscape)
- **Interview use**: second-order optimization methods (Adam approximates this)

---

## 3. Probability & Statistics

### Bayes Theorem
```
P(A|B) = P(B|A) · P(A) / P(B)
```
- Prior × Likelihood / Evidence = Posterior
- **Interview use**: Naive Bayes, MAP estimation vs MLE

### MLE vs MAP
- **MLE**: `argmax P(data | θ)` — maximize likelihood, no prior
- **MAP**: `argmax P(θ | data) = argmax P(data|θ)·P(θ)` — adds prior
- MAP with Gaussian prior = L2 regularization
- MAP with Laplace prior = L1 regularization

### Distributions You Must Know
| Distribution | Use Case |
|-------------|----------|
| Gaussian/Normal | Linear regression noise, weight init |
| Bernoulli | Binary classification output |
| Categorical | Multi-class output |
| Uniform | Random sampling |
| Beta | Prior for probabilities (Bayesian) |

### Expected Value & Variance
```
E[X] = Σ x·P(X=x)
Var(X) = E[(X - μ)²] = E[X²] - E[X]²
```

### Central Limit Theorem
- Sum of many independent random variables → Gaussian, regardless of original distribution
- **Interview use**: justifies why Gaussian noise assumption works in practice

### Information Theory
- **Entropy**: `H(X) = -Σ P(x) log P(x)` — uncertainty in a distribution
- **Cross-entropy**: `H(P,Q) = -Σ P(x) log Q(x)` — this IS your classification loss
- **KL Divergence**: `KL(P||Q) = Σ P(x) log(P(x)/Q(x))` — how different Q is from P
- Cross-entropy = Entropy + KL divergence

### Covariance & Correlation
```
Cov(X,Y) = E[(X-μₓ)(Y-μᵧ)]
Corr(X,Y) = Cov(X,Y) / (σₓ·σᵧ)  ∈ [-1, 1]
```

---

## 4. Key Statistical Concepts

### Bias-Variance Tradeoff
```
Expected Error = Bias² + Variance + Irreducible Noise
```
- **Bias**: error from wrong assumptions (underfitting) — model too simple
- **Variance**: error from sensitivity to training data (overfitting) — model too complex
- More complexity → lower bias, higher variance

### Hypothesis Testing
- **p-value**: probability of seeing this result if null hypothesis is true
- p < 0.05 → reject null (result is statistically significant)
- **Type I error (α)**: false positive — reject true null
- **Type II error (β)**: false negative — fail to reject false null

### Confidence Intervals
- 95% CI: if we repeat experiment 100 times, 95 intervals contain true parameter
- NOT: "95% probability true value is in this interval"

---

## Interview Quick-Fire Answers

**Q: What is the curse of dimensionality?**
As dimensions increase, data becomes sparse, distances lose meaning, and you need exponentially more data.

**Q: Why normalize features?**
Gradient descent converges faster when features are on same scale. Without it, loss landscape is elongated (oval) and oscillates.

**Q: What's the difference between correlation and causation?**
Correlation measures linear relationship strength. Causation requires controlled experiments or causal inference methods.
