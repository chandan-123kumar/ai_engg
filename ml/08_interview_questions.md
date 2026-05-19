# ML Interview Questions Bank

---

## FUNDAMENTALS (Every interview)

**Q: What is the bias-variance tradeoff?**
Expected error = Bias² + Variance + Irreducible noise.
- Bias: error from wrong assumptions (model too simple, underfits)
- Variance: error from over-sensitivity to training data (model too complex, overfits)
- Tradeoff: reducing bias often increases variance and vice versa

**Q: Explain overfitting and how to prevent it.**
Overfitting: model memorizes training data, performs poorly on unseen data.
Fixes: more data, regularization (L1/L2), dropout, early stopping, cross-validation, simpler model, data augmentation.

**Q: How do you handle class imbalance?**
- Resample: oversample minority (SMOTE) or undersample majority
- Class weights in loss function: `weight = n_samples / (n_classes * n_class_samples)`
- Use PR-AUC instead of accuracy for evaluation
- Threshold tuning: move decision boundary to optimize recall
- Collect more minority class data

**Q: What is regularization? Why does L1 produce sparse weights?**
Regularization adds penalty to loss for large weights → prevents overfitting.
L1 penalty has diamond-shaped contours. Optimal point where constraint touches loss function tends to land on a corner (axis) → coefficients hit exactly 0.

**Q: Explain cross-validation. Why not just use a validation set?**
CV trains on K-1 folds, validates on remaining fold, rotates K times. Averages results.
Why better: uses all data for both training and validation. Gives more reliable estimate of generalization error, especially with small datasets.

**Q: What's the difference between precision and recall? When do you prioritize each?**
- Precision: of predicted positive, how many are actually positive (minimize false alarms)
- Recall: of actual positive, how many did we catch (minimize misses)
- Prioritize precision: spam filtering (don't block legitimate emails)
- Prioritize recall: cancer screening, fraud detection (don't miss critical cases)

---

## ALGORITHMS

**Q: How does Random Forest reduce variance vs a single decision tree?**
Bagging: trains trees on random subsamples → each tree sees different data. Feature bagging: each split considers random feature subset → decorrelates trees. Averaging N independent noisy predictions reduces variance by factor of N (if uncorrelated). Key: the decorrelation from feature bagging is what makes it work beyond simple bagging.

**Q: What's the key difference between Random Forest and Gradient Boosting?**
RF: parallel trees, reduces variance. GBM: sequential trees, each corrects previous errors (reduces bias). GBM often more accurate but more prone to overfitting and slower to train.

**Q: How does XGBoost differ from vanilla gradient boosting?**
- Regularization terms in objective (L1/L2 on leaf weights)
- Second-order gradients (uses Hessian, not just gradient)
- Parallel split finding (approximate algorithm)
- Built-in handling of sparse data and missing values
- Column/row subsampling

**Q: When would you use SVM over logistic regression?**
- High-dimensional sparse data (text) — SVM works well with kernel trick
- When classes are linearly separable with clear margin
- When you need the kernel trick to handle non-linearly separable data
- LR better when you need calibrated probabilities or interpretability

**Q: Why can't we use squared error loss for classification?**
- Non-convex when applied to probabilities → multiple local minima
- Penalizes confident correct predictions (prediction=0.99, label=1 still has error 0.0001)
- Cross-entropy provides better gradients for classification

**Q: Explain the kernel trick in SVM.**
Instead of explicitly mapping data to high-dimensional space, compute dot products in that space directly via kernel function K(x,z) = φ(x)·φ(z). Never need to compute φ explicitly. RBF kernel implicitly maps to infinite-dimensional space.

---

## DEEP LEARNING

**Q: Why do we need activation functions? Why not just stack linear layers?**
Without activation functions, any number of linear layers = one linear layer (composition of linear maps is linear). Activation functions add non-linearity, allowing networks to learn complex functions.

**Q: Explain the vanishing gradient problem.**
In deep networks, gradients are products of Jacobians through each layer. With sigmoid/tanh, max gradient = 0.25. In a 10-layer network, gradient can be (0.25)^10 ≈ 10^-6. Early layers barely update. Fixes: ReLU, residual connections, batch norm, LSTM gates.

**Q: Why does batch normalization work?**
- Reduces internal covariate shift (distribution of activations changes during training)
- Allows higher learning rates → faster convergence
- Acts as regularizer (noise from batch statistics)
- Smooths loss landscape

**Q: What is the dying ReLU problem and how do you fix it?**
ReLU neurons can get stuck at 0 when inputs are always negative → gradient is always 0 → weights never update → neuron "dies." Causes: large learning rate, poor initialization.
Fixes: Leaky ReLU (small negative slope), ELU, proper He initialization, lower learning rate.

**Q: Explain skip/residual connections. Why do they help?**
`output = F(x) + x`. Allows gradients to flow directly through skip connection, bypassing any vanishing. Also allows network to learn identity function (just output input unchanged) → easier optimization. Enabled training of 100+ layer networks.

**Q: What is the difference between dropout in training vs inference?**
Training: randomly zero activations with probability p. Inference: no dropout, but scale outputs by (1-p) to match expected magnitude during training. In PyTorch, `model.eval()` disables dropout automatically.

---

## TRANSFORMERS & NLP

**Q: Explain self-attention in your own words.**
Each token generates a query (what am I looking for?), keys (what do I have?), and values (what do I share?). Queries and keys interact via dot product to compute attention weights (how relevant is each token to me?). Weighted sum of values is the output. Allows each token to gather information from all other tokens.

**Q: Why scale by √dₖ in attention?**
Dot products grow large with dimension dₖ → softmax outputs become near 0 or 1 (saturated) → very small gradients. Scaling keeps variance of dot products ≈ 1 regardless of dimension.

**Q: What's the difference between encoder-only and decoder-only transformers?**
- Encoder (BERT): bidirectional attention, sees full context, good for understanding tasks
- Decoder (GPT): causal/unidirectional attention, can only see past tokens, good for generation
- Encoder-decoder (T5): encoder encodes input, decoder generates output (seq2seq tasks)

**Q: What is temperature in LLM generation? Top-p sampling?**
Temperature T: `softmax(logits/T)`. T<1 → sharper distribution → more predictable. T>1 → flatter → more random.
Top-p (nucleus sampling): sample only from the smallest set of tokens whose cumulative probability exceeds p. More adaptive than top-k.

**Q: What is RAG and when would you use it over fine-tuning?**
RAG retrieves relevant documents at inference time, feeds them to LLM as context.
Use RAG when: knowledge changes frequently (can update vector DB without retraining), need source attribution, want to reduce hallucination, knowledge doesn't need to be baked into weights.
Use fine-tuning when: domain-specific behavior or style, skills/capabilities, faster inference (no retrieval), knowledge is static.

---

## ML SYSTEM DESIGN

**Q: How would you design a recommendation system for a new user? (cold start problem)**
- Content-based filtering with item metadata (no user history needed)
- Popularity-based recommendations as baseline
- Ask user for preferences during onboarding
- Use demographic similarities to similar users
- Explore-exploit: try different items, learn from early interactions quickly

**Q: What is feature/training-serving skew?**
Features computed differently during training (batch job using historical aggregations) vs serving (real-time, different logic). Model trained on distributions that don't match serving → degraded performance. Fix: use feature store, share computation logic, monitor feature distributions in both.

**Q: How would you handle model degradation in production?**
1. Monitor: feature distributions, prediction distributions, business metrics
2. Alert: statistical thresholds (PSI > 0.2) or metric drop
3. Diagnose: data drift, concept drift, code bugs
4. Fix: retrain on fresh data, update feature pipeline, rollback if needed
5. Prevent: automated retraining pipeline, shadow mode testing

**Q: How do you ensure reproducibility in ML?**
- Version control: code (git), data (DVC), models (MLflow)
- Pin dependencies: requirements.txt with exact versions
- Set random seeds (numpy, pytorch, python random)
- Log all hyperparameters and config
- Store training data split information

---

## MLOPS

**Q: What is data drift and how do you detect it?**
Data drift: P(X) changes — input distribution at inference differs from training.
Detection: compare feature distributions using KS test (continuous), chi-squared (categorical), or PSI (Population Stability Index). Monitor histograms of each feature over time.

**Q: Describe a CI/CD pipeline for ML.**
```
Code commit → unit tests → integration tests → 
data validation → training job → evaluation → 
if metrics pass → deploy to staging → canary test → 
gradual rollout → production monitoring → alerts
```

**Q: How do you do A/B testing for ML models?**
Randomly split users (not sessions) into control (existing model) and treatment (new model). Ensure sufficient sample size via power analysis. Define success metric and guardrails beforehand. Run until significance, don't stop early (peeking problem). Check for novelty effects.

---

## BEHAVIORAL / EXPERIENCE

**Q: Tell me about a time you deployed a model and it failed in production.**
Framework: situation → what went wrong → how you diagnosed it → how you fixed it → what you learned.
Common answers: training-serving skew, data pipeline bug, class distribution shift, edge case not in training data.

**Q: How do you evaluate whether a model is ready to deploy?**
- Offline: metrics meet threshold (F1, AUC, etc.)
- Shadow testing: run alongside current model, compare distributions
- Business simulation: estimate revenue/cost impact
- Edge cases: test on adversarial inputs, rare events
- Latency: meets SLA under load
- Monitoring: dashboards and alerts configured

---

## QUICK CHEAT SHEET

| Concept | One Line |
|---------|----------|
| Gradient descent | Iteratively move weights in direction that reduces loss |
| Backprop | Chain rule applied backward to compute all gradients |
| Overfitting | Memorized training set, fails to generalize |
| Regularization | Add penalty for large weights to prevent overfitting |
| Batch norm | Normalize activations per batch during training |
| Dropout | Randomly zero neurons to create implicit ensemble |
| Attention | Weighted sum of values, weights from query-key similarity |
| LSTM | RNN with gates to control long-term memory |
| Transfer learning | Start from pretrained weights, adapt to new task |
| Data drift | Input distribution changes after model deployed |
| RAG | Retrieve relevant documents, feed to LLM as context |
| LoRA | Low-rank weight updates for efficient fine-tuning |
