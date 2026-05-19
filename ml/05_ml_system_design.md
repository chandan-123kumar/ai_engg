# ML System Design — Interview Level

---

## Framework: How to Answer Any ML Design Question

### PASSTA Framework
1. **P**roblem definition — clarify the task, metrics, constraints
2. **A**rchitecture — high-level system design
3. **S**cale — data volume, traffic, latency requirements
4. **S**tack — data pipeline, training infrastructure, serving
5. **T**raining — features, model choice, training strategy
6. **A**ssessment — evaluation, monitoring, A/B testing

---

## Common ML Design Problems

### 1. Recommendation System (Netflix / YouTube)

**Problem**: Given a user, rank items by relevance.

**Two-stage architecture** (industry standard):
```
All Items (millions)
     ↓ Candidate Generation (fast, recall-focused)
  ~1000 candidates
     ↓ Ranking (slow, precision-focused)
   Top 100
     ↓ Reranking (business rules, diversity)
   Final 10-20
```

**Candidate Generation**
- Collaborative filtering: users who liked X also liked Y
- Content-based: similar items to what user liked
- Matrix factorization: SVD on user-item interaction matrix
- Two-tower model: embed users and items, retrieve nearest neighbors

**Ranking**
- Feature engineering: user features, item features, context (time, device), interaction features
- Model: GBDT or Deep & Cross Network
- Output: estimated CTR or engagement probability

**Features**
- User: age, location, watch history, search history, demographics
- Item: genre, actors, description embeddings, popularity
- Context: time of day, day of week, device, session length
- Interaction: has user watched similar items, rating history

**Metrics**
- Offline: NDCG, MAP, Recall@K
- Online: CTR, watch time, session length, retention

---

### 2. Search Ranking

**Query → retrieve → rank → serve**

**Retrieval**: BM25 (keyword matching) + dense retrieval (semantic similarity)

**Ranking features**:
- Query-document relevance (BM25 score, semantic similarity)
- Document quality (pagerank, freshness, click-through rate)
- User context (location, language, search history)
- Query intent (informational, navigational, transactional)

**Learning to Rank approaches**:
- Pointwise: predict relevance score per doc
- Pairwise: predict which of two docs is more relevant
- Listwise: optimize ranking metric directly (LambdaRank)

---

### 3. Fraud Detection

**Challenges**: extreme class imbalance (0.1% fraud), real-time requirements, adversarial

**Data**: transactions, user behavior, device fingerprints, network graphs

**Model**:
- Rule-based system (fast, interpretable) → ML model → human review
- GBMs (XGBoost) work well for tabular fraud features
- Graph neural networks for transaction network patterns
- Real-time: lightweight model for <100ms decisions

**Handling imbalance**:
- Oversample minority: SMOTE
- Undersample majority
- Class weights in loss function
- Threshold tuning (optimize F1 or precision@recall)

**Metrics**: Precision, Recall, F1 at given threshold. NOT accuracy (useless at 99.9% non-fraud). ROC-AUC, PR-AUC.

---

### 4. Ad Click-Through Rate (CTR) Prediction

**Core**: `P(click | user, ad, context)`

**Features**:
- User: demographics, browsing history, past clicks
- Ad: creative, landing page, historical CTR
- Context: page content, time, device

**Models**:
- Logistic Regression with feature crosses (Facebook 2014)
- Wide & Deep (Google): wide = memorization, deep = generalization
- DeepFM: factorization machines + deep learning
- DLRM (Meta): embedding tables for categorical features

**Training at scale**:
- Billions of samples → distributed training
- Continuous training: model must be fresh (data drift is severe)
- Feature pipeline latency: some features precomputed, some real-time

---

### 5. Image Classification / Object Detection

**Classification**: CNN backbone → global pooling → linear head
**Detection**: anchor-based (YOLO, Faster RCNN) or anchor-free (DETR)

**Transfer learning flow**:
1. Start with ImageNet pretrained backbone
2. Replace/add task head
3. Freeze backbone, train head (few epochs)
4. Unfreeze, fine-tune with 10× lower LR

---

## Data Pipeline Design

```
Raw Data Sources → Ingestion → Storage → Processing → Feature Store → Training/Serving
```

### Feature Store
- Online store (Redis/DynamoDB): low-latency serving features
- Offline store (S3/BigQuery): historical features for training
- Key requirement: training-serving feature parity (avoid skew)

### Feature Skew
Training uses historical data; serving uses real-time data. If computation differs → model degrades. **Fix**: share feature computation code between training and serving.

---

## Model Serving Architecture

### Batch vs Online Inference
- **Batch**: precompute predictions for all users nightly, store in DB
  - Fast serving, cheap compute, stale predictions
- **Online**: compute prediction at request time
  - Fresh predictions, higher latency, harder to scale

### Scaling Serving
- **Horizontal scaling**: multiple replicas behind load balancer
- **Model compression**: quantization (FP32→INT8, 4x smaller), pruning, distillation
- **Caching**: cache predictions for repeated inputs
- **GPU vs CPU serving**: GPU for transformers, CPU often enough for GBMs

### Latency Budget
```
Typical web app: 100ms total
  - Network: 20ms
  - Feature retrieval: 10ms
  - Model inference: 50ms
  - Post-processing: 20ms
```

---

## A/B Testing & Experiment Design

### Setting up an A/B test
1. Define success metric and guardrail metrics
2. Calculate required sample size (power analysis)
3. Randomize users (not sessions) into control/treatment
4. Run until statistical significance (don't peek early!)
5. Check for novelty effects and network effects

### Common pitfalls
- **Peeking**: stopping early when you see significance → inflates false positives
- **Network effects**: users interact → control group contaminated
- **SUTVA violation**: user in control sees treatment (e.g., a friend's feed)
- **Multiple metrics**: need correction (Bonferroni) for testing many metrics

### Shadow Mode
Route traffic to new model but don't use its predictions. Compare predictions with current model. Good for validating before launch.

---

## Monitoring & Model Maintenance

### Types of drift
- **Data drift**: input distribution changes (e.g., pandemic → user behavior shifts)
- **Concept drift**: relationship between X and y changes (e.g., fraud patterns evolve)
- **Label drift**: output distribution changes

### Detecting drift
- Statistical tests: KS test, PSI (Population Stability Index), chi-squared
- Monitor feature distributions with dashboards
- Watch prediction distribution — sudden shift = problem

### Metrics to monitor
- Model output distribution
- Feature distributions (per feature)
- Business metrics (CTR, revenue)
- Latency, error rate, throughput

### Retraining strategies
- **Schedule**: retrain weekly/daily regardless
- **Trigger-based**: retrain when drift detected
- **Online learning**: update model continuously with new data

---

## Interview Tips for System Design

1. **Clarify before designing**: ask about scale (users, QPS), latency (real-time?), data (labeled?), resources
2. **Start simple**: propose a simple baseline first, then improve
3. **Think out loud**: interviewers want to see your reasoning
4. **Know trade-offs**: every choice has pros/cons
5. **Bring up failure modes**: what could go wrong? How do you handle it?

**Sample clarifying questions**:
- "How many users do we serve? What's the expected QPS?"
- "Do we have labeled training data or do we need to collect it?"
- "What's the latency requirement — real-time or can we precompute?"
- "What does success look like? What's the primary metric?"
