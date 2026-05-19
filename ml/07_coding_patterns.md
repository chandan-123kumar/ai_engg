# Coding Patterns — ML Interview Level

---

## 1. Implement from Scratch (Most Common)

### Linear Regression with Gradient Descent
```python
import numpy as np

class LinearRegression:
    def __init__(self, lr=0.01, epochs=1000):
        self.lr = lr
        self.epochs = epochs
    
    def fit(self, X, y):
        n, d = X.shape
        self.w = np.zeros(d)
        self.b = 0.0
        
        for _ in range(self.epochs):
            y_pred = X @ self.w + self.b
            error = y_pred - y
            
            dw = (2/n) * X.T @ error
            db = (2/n) * error.sum()
            
            self.w -= self.lr * dw
            self.b -= self.lr * db
    
    def predict(self, X):
        return X @ self.w + self.b
```

### Logistic Regression
```python
class LogisticRegression:
    def __init__(self, lr=0.01, epochs=1000):
        self.lr = lr
        self.epochs = epochs
    
    def sigmoid(self, z):
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))  # clip for stability
    
    def fit(self, X, y):
        n, d = X.shape
        self.w = np.zeros(d)
        self.b = 0.0
        
        for _ in range(self.epochs):
            z = X @ self.w + self.b
            y_pred = self.sigmoid(z)
            error = y_pred - y
            
            self.w -= self.lr * (X.T @ error) / n
            self.b -= self.lr * error.sum() / n
    
    def predict_proba(self, X):
        return self.sigmoid(X @ self.w + self.b)
    
    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X) >= threshold).astype(int)
```

### K-Means
```python
class KMeans:
    def __init__(self, k=3, max_iter=100):
        self.k = k
        self.max_iter = max_iter
    
    def fit(self, X):
        # k-means++ initialization
        idx = np.random.randint(len(X))
        self.centroids = [X[idx]]
        
        for _ in range(self.k - 1):
            dists = np.array([min(np.linalg.norm(x - c)**2 for c in self.centroids) for x in X])
            probs = dists / dists.sum()
            self.centroids.append(X[np.random.choice(len(X), p=probs)])
        
        self.centroids = np.array(self.centroids)
        
        for _ in range(self.max_iter):
            labels = self._assign(X)
            new_centroids = np.array([X[labels == k].mean(axis=0) for k in range(self.k)])
            if np.allclose(self.centroids, new_centroids):
                break
            self.centroids = new_centroids
        
        self.labels_ = labels
    
    def _assign(self, X):
        dists = np.linalg.norm(X[:, np.newaxis] - self.centroids, axis=2)
        return np.argmin(dists, axis=1)
    
    def predict(self, X):
        return self._assign(X)
```

### Backpropagation (2-layer network)
```python
class TwoLayerNet:
    def __init__(self, input_dim, hidden_dim, output_dim, lr=0.01):
        self.W1 = np.random.randn(input_dim, hidden_dim) * np.sqrt(2/input_dim)  # He init
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, output_dim) * np.sqrt(2/hidden_dim)
        self.b2 = np.zeros(output_dim)
        self.lr = lr
    
    def relu(self, z):
        return np.maximum(0, z)
    
    def softmax(self, z):
        e = np.exp(z - z.max(axis=1, keepdims=True))  # numerically stable
        return e / e.sum(axis=1, keepdims=True)
    
    def forward(self, X):
        self.z1 = X @ self.W1 + self.b1
        self.a1 = self.relu(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = self.softmax(self.z2)
        return self.a2
    
    def backward(self, X, y):
        n = X.shape[0]
        # one-hot encode y
        y_onehot = np.zeros_like(self.a2)
        y_onehot[np.arange(n), y] = 1
        
        # output layer gradient
        dz2 = (self.a2 - y_onehot) / n
        dW2 = self.a1.T @ dz2
        db2 = dz2.sum(axis=0)
        
        # hidden layer gradient
        da1 = dz2 @ self.W2.T
        dz1 = da1 * (self.z1 > 0)  # ReLU derivative
        dW1 = X.T @ dz1
        db1 = dz1.sum(axis=0)
        
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
```

---

## 2. NumPy Patterns

### Vectorization (avoid loops)
```python
# Bad: slow Python loop
for i in range(n):
    result[i] = some_fn(X[i])

# Good: vectorized
result = some_fn(X)

# Pairwise distances (fast)
dists = np.linalg.norm(X[:, np.newaxis] - Y[np.newaxis, :], axis=2)

# Sigmoid
def sigmoid(x):
    return np.where(x >= 0,
                    1 / (1 + np.exp(-x)),
                    np.exp(x) / (1 + np.exp(x)))  # numerically stable

# Softmax (numerically stable)
def softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)
```

### Broadcasting rules
```python
A.shape = (3, 1, 5)
B.shape = (   4, 5)
# Result: (3, 4, 5)  — dimensions align from right, 1 broadcasts
```

---

## 3. Evaluation Metrics from Scratch

```python
def confusion_matrix(y_true, y_pred):
    tp = ((y_pred == 1) & (y_true == 1)).sum()
    fp = ((y_pred == 1) & (y_true == 0)).sum()
    fn = ((y_pred == 0) & (y_true == 1)).sum()
    tn = ((y_pred == 0) & (y_true == 0)).sum()
    return tp, fp, fn, tn

def precision_recall_f1(y_true, y_pred):
    tp, fp, fn, tn = confusion_matrix(y_true, y_pred)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2*precision*recall / (precision+recall) if (precision+recall) > 0 else 0
    return precision, recall, f1

def roc_auc(y_true, y_scores):
    thresholds = np.sort(y_scores)[::-1]
    tprs, fprs = [], []
    for t in thresholds:
        y_pred = (y_scores >= t).astype(int)
        tp, fp, fn, tn = confusion_matrix(y_true, y_pred)
        tprs.append(tp / (tp + fn))
        fprs.append(fp / (fp + tn))
    return np.trapz(tprs, fprs)  # area under curve
```

---

## 4. PyTorch Patterns

### Training loop template
```python
model = MyModel().to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
criterion = nn.CrossEntropyLoss()

for epoch in range(num_epochs):
    model.train()
    for X_batch, y_batch in train_loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    
    scheduler.step()
    
    model.eval()
    with torch.no_grad():
        val_loss = evaluate(model, val_loader)
```

### Custom Dataset
```python
class MyDataset(Dataset):
    def __init__(self, X, y, transform=None):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        self.transform = transform
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        x = self.X[idx]
        if self.transform:
            x = self.transform(x)
        return x, self.y[idx]
```

### Attention from scratch
```python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention(Q, K, V, mask=None):
    d_k = Q.size(-1)
    scores = Q @ K.transpose(-2, -1) / d_k**0.5  # (batch, heads, seq, seq)
    
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    
    attn_weights = F.softmax(scores, dim=-1)
    return attn_weights @ V, attn_weights
```

---

## 5. Common Interview Coding Problems

### Implement train/test split without sklearn
```python
def train_test_split(X, y, test_size=0.2, random_state=42):
    np.random.seed(random_state)
    n = len(X)
    idx = np.random.permutation(n)
    split = int(n * (1 - test_size))
    train_idx, test_idx = idx[:split], idx[split:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]
```

### Implement cross-validation
```python
def k_fold_cv(model, X, y, k=5):
    n = len(X)
    fold_size = n // k
    scores = []
    
    for i in range(k):
        val_idx = np.arange(i*fold_size, (i+1)*fold_size)
        train_idx = np.concatenate([np.arange(0, i*fold_size),
                                     np.arange((i+1)*fold_size, n)])
        model.fit(X[train_idx], y[train_idx])
        preds = model.predict(X[val_idx])
        scores.append((preds == y[val_idx]).mean())
    
    return np.mean(scores), np.std(scores)
```

### Implement cosine similarity
```python
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Batch version (fast)
def cosine_similarity_matrix(A, B):
    A_norm = A / np.linalg.norm(A, axis=1, keepdims=True)
    B_norm = B / np.linalg.norm(B, axis=1, keepdims=True)
    return A_norm @ B_norm.T
```

---

## 6. Tips for ML Coding Interviews

1. **Clarify before coding**: ask about edge cases, data types, scale
2. **Start simple**: working solution first, then optimize
3. **Talk through your logic**: interviewers want to hear your thought process
4. **Test with examples**: trace through a small example before full implementation
5. **Know numpy well**: vectorize loops, understand broadcasting
6. **Know PyTorch basics**: Dataset, DataLoader, model.train(), model.eval(), no_grad()
7. **Common gotchas**:
   - Numerical stability in sigmoid/softmax (clip or subtract max)
   - Transpose confusion: `X.T @ X` vs `X @ X.T`
   - Off-by-one in array indexing
   - Forgot `optimizer.zero_grad()` → gradients accumulate
