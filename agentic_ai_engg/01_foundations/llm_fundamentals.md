# LLM Fundamentals — Interview Guide

## Must-Know Concepts

### Transformer Architecture
- **Self-attention**: each token attends to all others via Q, K, V matrices
- **Multi-head attention**: runs attention in parallel subspaces, then concatenates
- **Positional encoding**: injects position info (sinusoidal or learned RoPE/ALiBi)
- **Feed-forward layers**: two linear transformations with GELU/ReLU in between
- **Layer norm**: applied pre- or post-attention (pre-norm more stable in large models)

### Key Formula
```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V
```
`sqrt(d_k)` scaling prevents vanishing gradients in dot products.

### Inference Mechanics
| Concept | What it is | Why it matters |
|---|---|---|
| Autoregressive | Generate one token at a time | Latency scales with output length |
| KV Cache | Cache past K,V to avoid recomputation | Critical for long contexts |
| Temperature | Scales logits before softmax | Controls randomness |
| Top-p (nucleus) | Sample from top-p probability mass | Better than top-k for diversity |
| Beam search | Explore multiple paths | Slower but more coherent long outputs |

### Context Window
- GPT-4: 128k tokens, Claude: 200k tokens, Gemini 1.5: 1M tokens
- **Longer ≠ better retrieval** — "lost in the middle" problem: models attend poorly to info in the middle of long contexts
- For agents: long context is expensive; RAG is often better than stuffing everything in context

### Tokenization
- BPE (GPT), WordPiece (BERT), SentencePiece (Llama)
- ~1 token ≈ 0.75 words in English
- Non-English languages tokenize less efficiently (more tokens per word)
- Implication for agents: count tokens for cost/latency estimation

### Fine-tuning vs Prompting
| Approach | When to use | Trade-off |
|---|---|---|
| Zero-shot | General capability | No examples needed |
| Few-shot | Consistent format needed | Uses context tokens |
| Fine-tuning (SFT) | Domain-specific style/knowledge | Expensive, needs data |
| RLHF/DPO | Alignment, preference learning | Very expensive |
| LoRA/QLoRA | Efficient fine-tuning | Parameter-efficient |

### Common Interview Questions

**Q: What is the attention complexity and why does it matter for agents?**
A: O(n²) in sequence length. For long-running agent loops with large context, this makes each step expensive. Solutions: sparse attention, sliding window, or RAG to limit context size.

**Q: Why do LLMs hallucinate?**
A: They predict the most statistically likely next token, not what is factually true. They have no grounding mechanism unless given tools or retrieved context. Hallucination increases when asked about specific facts, recent events, or low-frequency knowledge.

**Q: What's the difference between temperature=0 and greedy decoding?**
A: Temperature=0 makes the softmax output near-deterministic (approaches argmax). Greedy decoding strictly picks the argmax. Both give near-identical results but temperature=0 is numerically more stable.

**Q: How does KV cache help agents?**
A: In multi-turn agent conversations, the system prompt and prior turns are re-encoded at each step without KV cache. With KV cache, only the new tokens are processed, reducing latency and cost dramatically. Anthropic's prompt caching leverages this explicitly.

## Numbers to Know
- GPT-4o: ~$5/M input tokens, ~$15/M output tokens
- Claude Sonnet 4.6: ~$3/M input, ~$15/M output
- Embedding models: ~$0.02/M tokens (100x cheaper)
- Typical agent turn: 1k–5k input tokens, 200–1k output tokens
- Human reading speed: ~250 words/min ≈ 333 tokens/min
