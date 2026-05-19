# MLOps — Interview Level

---

## 1. The ML Lifecycle

```
Problem Definition
      ↓
Data Collection & Labeling
      ↓
EDA & Feature Engineering
      ↓
Model Development (train/eval)
      ↓
Model Validation
      ↓
Deployment
      ↓
Monitoring & Maintenance
      ↑_______________|  (continuous loop)
```

---

## 2. Data Engineering for ML

### Data Versioning
- **DVC (Data Version Control)**: like git for datasets and models
- Store data in S3/GCS, track pointers in git
- Reproducibility: can recreate any experiment with exact same data

### Data Validation
- **Great Expectations**: define data "expectations" (schema, ranges, distributions)
- Run before every training run
- Fail fast: catch data issues before wasting training compute

### Data Labeling
- Human annotation: Amazon Mechanical Turk, Scale AI, Label Studio
- Active learning: model picks uncertain samples to label first (most efficient)
- Weak supervision: Snorkel — programmatic labeling with noisy sources
- Semi-supervised: use unlabeled data with small labeled set

---

## 3. Feature Engineering

### Feature Types
- Numerical: normalize/standardize, handle outliers, log-transform skewed
- Categorical: one-hot (low cardinality), target encoding (high cardinality), embedding
- Text: TF-IDF, word embeddings, BERT embeddings
- Time: lag features, rolling stats, hour/day/month, cyclical encoding

### Cyclical Encoding
Hour of day is cyclical (23 and 0 are adjacent):
```python
hour_sin = sin(2π × hour / 24)
hour_cos = cos(2π × hour / 24)
```

### Target Encoding
Replace category with mean target value for that category:
- **Problem**: data leakage if done before train/test split
- **Fix**: use out-of-fold encoding (compute encoding on other folds)

### Handling Missing Values
- Mean/median imputation (simple, often fine)
- Model-based imputation (more accurate)
- Indicator variable: add `feature_is_missing` binary column
- Leave as NaN: tree-based models handle it natively

### Feature Selection
- Correlation analysis: remove highly correlated features
- Feature importance from trees (Gini, permutation)
- Recursive Feature Elimination (RFE)
- L1 regularization (Lasso)

---

## 4. Training Infrastructure

### Distributed Training

**Data Parallelism** (most common):
- Split dataset across devices, copy model to each
- Each device computes gradients on its batch
- Aggregate gradients (AllReduce), update weights
- PyTorch: `DistributedDataParallel (DDP)`

**Model Parallelism** (for models too large for one GPU):
- Split model layers across devices
- Pipeline parallelism: each stage processes different micro-batches
- Tensor parallelism: split individual layers (attention heads) across GPUs

**ZeRO (Zero Redundancy Optimizer)**:
- Stage 1: partition optimizer states
- Stage 2: + partition gradients
- Stage 3: + partition model parameters
- Used in DeepSpeed for training LLMs on many GPUs

### Compute Options
- **On-premise**: high upfront cost, full control, good for steady workloads
- **Cloud (AWS/GCP/Azure)**: pay per use, flexible, managed services
- **Spot/Preemptible instances**: 60-80% cheaper, can be interrupted → need checkpointing

### Experiment Tracking
Tools: **MLflow**, **Weights & Biases (W&B)**, Neptune
Track: hyperparameters, metrics per epoch, artifacts (model weights, plots), code version

```python
# W&B example
import wandb
wandb.init(project="my-model", config={"lr": 0.001, "epochs": 10})
wandb.log({"train_loss": loss, "val_acc": acc})
wandb.finish()
```

### Hyperparameter Tuning
- **Grid search**: exhaustive, exponential scaling
- **Random search**: often better than grid for same budget
- **Bayesian optimization**: model the search space, sample promising areas
  - Tools: Optuna, Ray Tune, Hyperopt
- **Population-based training**: evolve population of models

---

## 5. Model Evaluation

### Metrics by Task Type

**Classification**
```
Accuracy = (TP+TN) / (TP+TN+FP+FN)
Precision = TP / (TP+FP)     ← of predicted positive, how many are?
Recall = TP / (TP+FN)        ← of actual positive, how many did we catch?
F1 = 2 × (P×R) / (P+R)

ROC-AUC: area under ROC curve (TPR vs FPR at all thresholds)
PR-AUC: area under Precision-Recall curve (better for imbalanced)
```

**When to use what**:
- **Accuracy**: balanced classes
- **Precision**: cost of false positive is high (spam detection: don't want to block legit emails)
- **Recall**: cost of false negative is high (cancer detection: don't miss cases)
- **F1**: balance both
- **AUC-ROC**: when you need threshold-agnostic evaluation
- **PR-AUC**: imbalanced classes (fraud, rare disease)

**Regression**
- MSE: penalizes large errors heavily (outlier-sensitive)
- MAE: robust to outliers
- RMSE: same units as target, penalizes large errors
- MAPE: relative error (useful when scale varies)
- R²: proportion of variance explained (1 is perfect, 0 is baseline mean)

### Cross-Validation
```
K-Fold: split data into K folds, train on K-1, validate on 1, rotate
Stratified K-Fold: maintain class distribution in each fold
Time-series CV: always validate on future data (no future leakage)
```

---

## 6. Model Deployment

### Serving Patterns

**REST API**: Flask/FastAPI → model inference endpoint
```python
@app.post("/predict")
def predict(features: Features):
    return {"prediction": model.predict([features.values])[0]}
```

**gRPC**: Protocol Buffers, faster than REST for internal services

**Batch inference**: Spark/Beam job processes millions of records offline

**Streaming**: Kafka + Flink for real-time feature updates and predictions

### Model Formats
- **ONNX**: model exchange format, run on any runtime
- **TorchScript**: PyTorch → serialized, no Python dependency
- **TF SavedModel**: TensorFlow serving format
- **PMML**: classical ML models
- **BentoML / TorchServe**: model serving frameworks

### Containerization
```dockerfile
FROM python:3.10
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY model.pkl .
COPY app.py .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]
```

### Model Versioning
- Canary deployment: route 5% traffic to new model
- Blue/green: maintain two environments, switch traffic
- Shadow mode: new model predicts but not served

---

## 7. Monitoring in Production

### What to Monitor

**Model health**:
- Prediction distribution (histogram of model outputs)
- Confidence/probability distribution
- Prediction latency (P50, P95, P99)

**Data health**:
- Feature distributions (compared to training baseline)
- Missing value rates
- Schema violations

**Business health**:
- Primary metric (CTR, conversion rate)
- Downstream KPIs
- Revenue impact

### Alerting Thresholds
- PSI > 0.2: significant drift, investigate immediately
- PSI 0.1-0.2: moderate drift, monitor closely
- PSI < 0.1: no significant drift

### Tools
- **Evidently AI**: open source drift detection
- **Arize AI / Fiddler**: commercial model monitoring
- **Prometheus + Grafana**: infrastructure metrics
- **DataDog**: APM + custom ML metrics

---

## 8. CI/CD for ML

### ML Pipeline (Kubeflow / MLflow / Airflow)
```
Data Validation → Feature Engineering → Training → Evaluation → 
→ [If metrics pass] → Model Registry → Deployment → Monitoring
```

### Model Registry
Store trained models with:
- Version number
- Training data version
- Hyperparameters
- Evaluation metrics
- Artifacts

Tools: MLflow Model Registry, W&B Artifacts, SageMaker Model Registry

### Automated Retraining Pipeline
```
Trigger: scheduled / drift detected / performance degraded
  → Pull new data
  → Validate data
  → Retrain model
  → Evaluate vs current champion
  → If better → promote to production
  → If worse → alert and keep current
```

---

## Key MLOps Interview Questions

**Q: What is training-serving skew?**
When features computed differently at training time vs serving time. Fix: use feature store with shared computation logic.

**Q: How do you detect model degradation in production?**
Monitor prediction distribution shift, compare to baseline. Track business metrics. Use statistical tests (KS test, PSI) on features.

**Q: What is the difference between data drift and concept drift?**
Data drift: P(X) changes (input distribution changes). Concept drift: P(Y|X) changes (same input → different output should be).

**Q: How do you handle a model that's degrading but you don't have labels yet?**
- Monitor proxy metrics (user behavior, engagement)
- Monitor input drift as early warning signal
- Set up delayed label collection pipeline
- Have fallback model ready

**Q: How would you deploy a model that needs to be updated daily?**
Automated retraining pipeline: daily trigger → fetch new data → retrain → auto-evaluate → if threshold met, auto-deploy (blue/green) → monitor first hour for anomalies.
