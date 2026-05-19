# Classical ML Algorithms — Interview Level

---

## 1. Linear Regression

### How it works
```
ŷ = Xθ    →    minimize ||y - Xθ||²
Closed form: θ = (XᵀX)⁻¹Xᵀy
```

### Assumptions (interviewers love this)
1. Linearity between features and target
2. Independence of errors
3. Homoscedasticity (constant variance of errors)
4. Normality of errors (for inference, not prediction)
5. No multicollinearity

### Ridge vs Lasso vs Elastic Net
| | Loss | Effect | When to use |
|--|------|--------|-------------|
| **Ridge (L2)** | MSE + λ||θ||² | Shrinks weights, keeps all | correlated features |
| **Lasso (L1)** | MSE + λ||θ||₁ | Drives weights to zero | feature selection |
| **Elastic Net** | MSE + λ₁||θ||₁ + λ₂||θ||² | Both | many correlated features |

**Why L1 gives sparsity**: L1 contours are diamond-shaped; optimal point tends to hit a corner (axis), zeroing out features.

---

## 2. Logistic Regression

### How it works
```
P(y=1|x) = σ(xᵀθ) = 1 / (1 + e^(-xᵀθ))
Loss: -[y·log(ŷ) + (1-y)·log(1-ŷ)]  ← Binary Cross Entropy
```

### Key points
- Output is a probability, not a class → threshold at 0.5 by default
- Decision boundary is linear
- No closed form → use gradient descent
- Outputs are calibrated probabilities (unlike SVM)

### Multi-class: OvA vs Softmax
- **One-vs-All**: train K binary classifiers, take max
- **Softmax**: single model, `P(y=k) = e^(xᵀθₖ) / Σe^(xᵀθⱼ)`

---

## 3. Decision Trees

### Splitting criteria
- **Gini impurity**: `1 - Σ pᵢ²` (faster to compute)
- **Entropy/Information Gain**: `H(parent) - weighted_avg H(children)`
- **MSE reduction**: for regression trees

### Key hyperparameters
- `max_depth`: controls overfitting (deep = overfit)
- `min_samples_split`: minimum samples to split a node
- `min_samples_leaf`: minimum samples in leaf

### Pros/Cons
- ✅ No feature scaling needed, handles missing values, interpretable
- ❌ High variance, overfits easily, not smooth predictions

---

## 4. Random Forest

### How it works
1. Bootstrap sampling: take N random samples with replacement (bagging)
2. Train a decision tree on each sample
3. At each split, consider only √p random features (feature bagging)
4. Aggregate: majority vote (classification) or mean (regression)

### Why it works
- Bagging reduces variance without increasing bias
- Feature randomness decorrelates trees (key insight!)
- Individual trees overfit but ensemble averages out errors

### Feature Importance
```python
importance[feature] = avg reduction in impurity across all splits using that feature
```
**Caveat**: biased toward high-cardinality features. Use permutation importance for better estimates.

---

## 5. Gradient Boosting (XGBoost/LightGBM)

### How it works
1. Start with a weak learner (typically shallow tree)
2. Compute residuals (pseudo-gradients of loss)
3. Fit next tree to predict residuals
4. Add tree with learning rate: `F_m(x) = F_{m-1}(x) + α·h_m(x)`
5. Repeat

### XGBoost vs LightGBM vs CatBoost
| | XGBoost | LightGBM | CatBoost |
|--|---------|----------|---------|
| Splitting | Level-wise | Leaf-wise | Ordered |
| Speed | Moderate | Fast | Slower |
| Categorical | Manual encode | Native | Native |
| Best for | Tabular, structured | Large datasets | Categorical-heavy |

### Key hyperparameters
- `n_estimators`: number of trees (more → less bias, more variance, slower)
- `learning_rate`: shrinks each tree's contribution
- `max_depth`: tree depth (LightGBM: use `num_leaves` instead)
- `subsample`: row sampling ratio
- `colsample_bytree`: feature sampling ratio
- `reg_alpha/lambda`: L1/L2 regularization

---

## 6. Support Vector Machines (SVM)

### How it works
Find the hyperplane that maximizes margin between classes:
```
maximize: 2/||w||  (margin)
subject to: yᵢ(wᵀxᵢ + b) ≥ 1
```

### Kernel Trick
Map data to higher dimensions implicitly:
- **Linear**: `K(x,z) = xᵀz`
- **RBF/Gaussian**: `K(x,z) = exp(-γ||x-z||²)` ← most popular
- **Polynomial**: `K(x,z) = (xᵀz + c)ᵈ`

### C parameter
- Small C: wide margin, more misclassifications (underfitting)
- Large C: narrow margin, fewer misclassifications (overfitting)

### When to use SVM
- Small to medium datasets
- High-dimensional data (text classification)
- When you need a clear margin of separation

---

## 7. K-Nearest Neighbors (KNN)

### How it works
- Store all training points
- For new point: find K nearest (Euclidean/Manhattan distance)
- Predict: majority vote (classification) or mean (regression)

### Key issues
- **No training** — all computation at inference (lazy learner)
- Slow at inference for large datasets
- Sensitive to irrelevant features and scale (ALWAYS normalize)
- Curse of dimensionality hurts performance

### Choosing K
- Small K: low bias, high variance (overfit)
- Large K: high bias, low variance (underfit)
- Use cross-validation; odd K to avoid ties

---

## 8. K-Means Clustering

### Algorithm
```
1. Initialize K centroids randomly
2. Assign each point to nearest centroid
3. Update centroids = mean of assigned points
4. Repeat until convergence
```

### Choosing K
- **Elbow method**: plot inertia vs K, pick elbow point
- **Silhouette score**: measure how similar point is to its cluster vs others (range: -1 to 1)

### Limitations
- Assumes spherical clusters
- Sensitive to outliers and initialization
- Must specify K in advance
- Can get stuck in local minima → use k-means++

### K-Means++ initialization
Pick first centroid randomly, then each subsequent centroid with probability proportional to distance² from nearest existing centroid. Guarantees O(log K) approximation.

---

## 9. Naive Bayes

### How it works
```
P(y|x₁,...,xₙ) ∝ P(y) · ΠP(xᵢ|y)
```
**Naive assumption**: features are conditionally independent given the class.

### Variants
- **Gaussian NB**: features are continuous, Gaussian distributed
- **Multinomial NB**: word counts in text
- **Bernoulli NB**: binary features

### Why "naive" assumption works despite being wrong
- Even if probabilities are wrong, ranking is often correct
- Very robust with small data
- Fast and interpretable

---

## 10. PCA (Principal Component Analysis)

### How it works
1. Center data (subtract mean)
2. Compute covariance matrix: `C = XᵀX / (n-1)`
3. Find eigenvectors of C (principal components)
4. Project data onto top-k eigenvectors

### Key concepts
- Eigenvectors = directions of maximum variance
- Eigenvalues = amount of variance explained in each direction
- PCA is a linear transformation; captures only linear structure

### PCA vs t-SNE vs UMAP
| | PCA | t-SNE | UMAP |
|--|-----|-------|------|
| Type | Linear | Non-linear | Non-linear |
| Speed | Fast | Slow | Moderate |
| Preserves | Global structure | Local structure | Both (better) |
| Use | Feature reduction | Visualization | Visualization |
| Reproducible | Yes | No (stochastic) | Partial |

---

## Interview Comparison Questions

**Q: Random Forest vs Gradient Boosting?**
- RF: parallel trees, high variance → reduce via averaging, robust to overfitting
- GBM: sequential, each corrects previous, powerful but can overfit
- Rule of thumb: GBM wins on accuracy, RF wins on speed and robustness

**Q: Logistic Regression vs SVM?**
- LR: probabilistic output, works well when classes overlap, L2 regularized
- SVM: margin-based, no probability (unless Platt scaling), better in high-dim sparse data

**Q: When would you use a linear model over a tree-based one?**
When features have a linear relationship with the target, when you need interpretability, or when you have very limited data.
