# NLP & Transformers — Interview Level

---

## 1. Text Representations

### Word Embeddings
- **One-hot**: sparse, no semantic meaning, high dimension
- **Word2Vec**: dense, semantic meaning via co-occurrence
  - CBOW: predict center word from context
  - Skip-gram: predict context words from center word
- **GloVe**: combines global co-occurrence statistics
- **FastText**: subword embeddings, handles OOV words
- **BERT/GPT**: contextual embeddings — same word = different vector in different contexts

### Why word2vec captures semantics
**king - man + woman ≈ queen**
Training signal forces words with similar contexts to have similar vectors.

---

## 2. Attention Mechanism

### Intuition
Instead of compressing all input into one vector, let the decoder look at all encoder states and decide which are relevant.

### Scaled Dot-Product Attention
```
Attention(Q, K, V) = softmax(QKᵀ / √dₖ) · V
```
- Q (Query): what am I looking for?
- K (Key): what do I have to offer?
- V (Value): what information do I actually pass?
- √dₖ scaling: prevents softmax from saturating in high dimensions

### Why scale by √dₖ?
Dot products grow large with dₖ → softmax outputs become near-binary → vanishing gradients. Scaling keeps values in good range.

### Multi-Head Attention
```
MultiHead(Q,K,V) = Concat(head₁,...,headₕ) · Wᴼ
headᵢ = Attention(Q·Wᵢᵠ, K·Wᵢᴷ, V·Wᵢᵛ)
```
- Multiple heads learn different types of relationships simultaneously
- e.g., one head for syntax, one for coreference, one for semantics

---

## 3. Transformer Architecture

### Encoder block
```
Input → Embeddings + Positional Encoding
      → [Self-Attention → Add&Norm → FFN → Add&Norm] × N layers
```

### Decoder block
```
Tokens → Embeddings + Positional Encoding
       → [Masked Self-Attention → Add&Norm
          → Cross-Attention (attends to encoder) → Add&Norm
          → FFN → Add&Norm] × N layers
→ Linear → Softmax → probabilities
```

### Positional Encoding
Transformers have no recurrence → add position information:
```
PE(pos, 2i)   = sin(pos / 10000^(2i/dmodel))
PE(pos, 2i+1) = cos(pos / 10000^(2i/dmodel))
```
- Sinusoidal: no learned params, generalizes to longer sequences
- Alternative: learned positional embeddings (BERT style)
- Modern: RoPE (Rotary Position Embeddings) — encodes relative positions

### Feed-Forward Network in Transformer
```
FFN(x) = max(0, xW₁ + b₁)W₂ + b₂
```
- Same FFN applied to each position independently
- Hidden dim = 4×model_dim typically
- Acts as key-value memory (where model stores facts)

### Add & Norm (Residual + Layer Norm)
```
output = LayerNorm(x + Sublayer(x))
```
- Residual: helps gradient flow
- Layer Norm: stabilizes training

---

## 4. BERT vs GPT

| | BERT | GPT |
|--|------|-----|
| Architecture | Encoder only | Decoder only |
| Training | Masked LM + NSP | Causal LM (next token) |
| Attention | Bidirectional | Unidirectional (causal mask) |
| Use case | Classification, NER, Q&A | Generation, completion |
| Fine-tuning | Add task head | Prompt or fine-tune |

### BERT pretraining
- **Masked Language Model (MLM)**: mask 15% of tokens, predict them
- **Next Sentence Prediction (NSP)**: predict if sentence B follows A

### GPT pretraining
- **Causal LM**: predict next token given all previous tokens
- Autoregressive: generates one token at a time

---

## 5. Modern LLM Concepts

### Tokenization
- **BPE (Byte-Pair Encoding)**: merge most frequent byte pairs iteratively
- **WordPiece** (BERT): similar, uses likelihood instead of frequency
- **SentencePiece**: language-agnostic, handles any language

### Context Length & Attention Complexity
- Standard attention: O(n²) in sequence length
- Problem: 128K context = 128K² attention operations
- Solutions: Flash Attention, Sparse Attention, Linear Attention

### Flash Attention
Reorders attention computation to minimize memory reads/writes — same result, 10x faster, doesn't store full attention matrix in HBM.

### KV Cache
During inference, recompute K,V for previously generated tokens is wasteful → cache them. Memory: O(layers × heads × seq_len × d_head).

### Instruction Fine-tuning
- **SFT (Supervised Fine-tuning)**: train on (prompt, completion) pairs
- **RLHF**: human feedback → reward model → PPO to optimize policy
- **DPO**: skips reward model, directly optimizes on preferred vs rejected pairs

### PEFT (Parameter Efficient Fine-Tuning)
**LoRA**: freeze base model, inject trainable low-rank matrices:
```
W' = W + ΔW = W + BA
B ∈ ℝ^(d×r), A ∈ ℝ^(r×k), r << min(d,k)
```
Only train B, A → 100-1000x fewer parameters than full fine-tuning.

**QLoRA**: quantize base model to 4-bit, apply LoRA on top.

---

## 6. Evaluation Metrics for NLP

### Classification
- Accuracy, F1, Precision, Recall
- ROC-AUC for binary

### Generation
- **BLEU**: n-gram overlap with reference (machine translation)
- **ROUGE**: recall-oriented n-gram overlap (summarization)
- **Perplexity**: `exp(-1/N · Σ log P(wᵢ|w<ᵢ))` — how "surprised" model is
  - Lower perplexity = better language model
- **BERTScore**: semantic similarity using BERT embeddings
- **Human eval**: most reliable, measures coherence, helpfulness, safety

---

## 7. Key NLP Tasks & Approaches

### Named Entity Recognition (NER)
Token classification: each token gets a label (B-PER, I-PER, O, ...)
BiLSTM-CRF was dominant pre-BERT; now fine-tuned BERT.

### Question Answering
- Extractive: find span in context (BERT → predict start/end token)
- Generative: generate answer (T5, GPT)

### Summarization
- Extractive: select important sentences
- Abstractive: generate new text (seq2seq models like T5)

### Retrieval-Augmented Generation (RAG)
```
Query → Retriever (dense/sparse) → Top-k docs → LLM + docs → Answer
```
- Dense retrieval: encode query & docs as embeddings, cosine similarity
- Sparse retrieval: BM25 (TF-IDF based)
- Hybrid: combine both

---

## Interview Quick-Fire

**Q: What is the difference between self-attention and cross-attention?**
Self-attention: Q, K, V all come from same sequence (token attends to other tokens in same sequence). Cross-attention: Q from decoder, K and V from encoder (decoder attends to encoder outputs).

**Q: Why can't transformers handle very long contexts easily?**
Attention is O(n²) in sequence length — quadratic memory and compute. 10K tokens needs 100M attention scores.

**Q: What is temperature in LLM generation?**
`softmax(logits / T)`. T<1: sharper distribution (more confident, repetitive). T>1: flatter distribution (more random, creative). T=0: argmax (greedy).

**Q: What is hallucination and why does it happen?**
Model generates plausible-sounding but incorrect information. Happens because training objective (next token prediction) doesn't distinguish factual from plausible, and model can't know what it doesn't know.

**Q: BERT vs GPT — which would you use for sentiment analysis?**
BERT — it's an encoder-only model suited for classification tasks. Add linear head on [CLS] token and fine-tune. GPT can do it too via prompting but BERT is more parameter-efficient for this task.
