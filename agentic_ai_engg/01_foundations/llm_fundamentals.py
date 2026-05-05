"""
LLM Fundamentals — Hands-on Code Practice
Companion to: llm_fundamentals.md

Run each section independently or top-to-bottom.
Dependencies: pip install numpy tiktoken anthropic
"""

import math
import numpy as np

# ─────────────────────────────────────────────────────────────
# SECTION 1: Attention Mechanism — from scratch
# ─────────────────────────────────────────────────────────────

def softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max(axis=-1, keepdims=True))  # numerically stable
    return e / e.sum(axis=-1, keepdims=True)


def scaled_dot_product_attention(
    Q: np.ndarray,  # (seq_len, d_k)
    K: np.ndarray,  # (seq_len, d_k)
    V: np.ndarray,  # (seq_len, d_v)
    mask: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V

    Returns (output, attention_weights).
    mask: boolean array of shape (seq_len, seq_len); True = masked out (causal).
    """
    d_k = Q.shape[-1]
    scores = Q @ K.T / math.sqrt(d_k)           # (seq_len, seq_len)

    if mask is not None:
        scores = np.where(mask, -1e9, scores)    # fill masked positions with -inf

    weights = softmax(scores)                    # (seq_len, seq_len)
    output = weights @ V                         # (seq_len, d_v)
    return output, weights


def causal_mask(seq_len: int) -> np.ndarray:
    """Upper-triangular mask (True = future token, should be masked)."""
    return np.triu(np.ones((seq_len, seq_len), dtype=bool), k=1)


def demo_attention():
    print("=" * 60)
    print("SECTION 1: Scaled Dot-Product Attention")
    print("=" * 60)

    np.random.seed(42)
    seq_len, d_model, d_k = 4, 8, 4

    # Learned projection weights (in practice these are trained)
    W_Q = np.random.randn(d_model, d_k)
    W_K = np.random.randn(d_model, d_k)
    W_V = np.random.randn(d_model, d_k)

    # Input: 4 tokens, each with d_model=8 dimensional embedding
    X = np.random.randn(seq_len, d_model)

    Q = X @ W_Q   # (4, 4)
    K = X @ W_K   # (4, 4)
    V = X @ W_V   # (4, 4)

    # Full (bidirectional) attention — like BERT
    output_bi, weights_bi = scaled_dot_product_attention(Q, K, V)
    print(f"\nBidirectional attention output shape: {output_bi.shape}")
    print("Attention weights (each row sums to 1):")
    print(np.round(weights_bi, 3))

    # Causal (autoregressive) attention — like GPT
    mask = causal_mask(seq_len)
    output_causal, weights_causal = scaled_dot_product_attention(Q, K, V, mask)
    print("\nCausal mask (True = masked future tokens):")
    print(mask)
    print("Causal attention weights (lower-triangular):")
    print(np.round(weights_causal, 3))


# ─────────────────────────────────────────────────────────────
# SECTION 2: Multi-Head Attention
# ─────────────────────────────────────────────────────────────

class MultiHeadAttention:
    """
    Splits d_model into h heads, runs attention in parallel, concatenates.
    Each head learns a different representation subspace.
    """

    def __init__(self, d_model: int, num_heads: int):
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        # One weight matrix per head per projection (simplified)
        self.W_Q = [np.random.randn(d_model, self.d_k) for _ in range(num_heads)]
        self.W_K = [np.random.randn(d_model, self.d_k) for _ in range(num_heads)]
        self.W_V = [np.random.randn(d_model, self.d_k) for _ in range(num_heads)]
        self.W_O = np.random.randn(d_model, d_model)  # output projection

    def forward(self, X: np.ndarray, causal: bool = False) -> np.ndarray:
        seq_len = X.shape[0]
        mask = causal_mask(seq_len) if causal else None

        head_outputs = []
        for i in range(self.num_heads):
            Q = X @ self.W_Q[i]
            K = X @ self.W_K[i]
            V = X @ self.W_V[i]
            out, _ = scaled_dot_product_attention(Q, K, V, mask)
            head_outputs.append(out)

        # Concatenate all heads → (seq_len, d_model)
        concat = np.concatenate(head_outputs, axis=-1)
        return concat @ self.W_O


def demo_multi_head():
    print("\n" + "=" * 60)
    print("SECTION 2: Multi-Head Attention")
    print("=" * 60)

    np.random.seed(0)
    seq_len, d_model, num_heads = 6, 16, 4

    mha = MultiHeadAttention(d_model, num_heads)
    X = np.random.randn(seq_len, d_model)

    output = mha.forward(X, causal=True)
    print(f"\nInput shape:  {X.shape}  (seq_len={seq_len}, d_model={d_model})")
    print(f"Heads:        {num_heads}  (d_k per head = {d_model // num_heads})")
    print(f"Output shape: {output.shape}  (same as input — shape preserved)")


# ─────────────────────────────────────────────────────────────
# SECTION 3: Positional Encoding (Sinusoidal)
# ─────────────────────────────────────────────────────────────

def sinusoidal_positional_encoding(seq_len: int, d_model: int) -> np.ndarray:
    """
    PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

    Injected into token embeddings so the model knows token order.
    """
    PE = np.zeros((seq_len, d_model))
    positions = np.arange(seq_len)[:, np.newaxis]          # (seq_len, 1)
    dims = np.arange(0, d_model, 2)                        # even indices
    div_term = np.power(10000.0, dims / d_model)

    PE[:, 0::2] = np.sin(positions / div_term)
    PE[:, 1::2] = np.cos(positions / div_term)
    return PE


def demo_positional_encoding():
    print("\n" + "=" * 60)
    print("SECTION 3: Positional Encoding")
    print("=" * 60)

    PE = sinusoidal_positional_encoding(seq_len=8, d_model=16)
    print(f"\nPE shape: {PE.shape}  (8 positions × 16 dims)")
    print("First 4 positions, first 8 dims:")
    print(np.round(PE[:4, :8], 3))
    print("\nKey property: dot product between positions decays with distance")
    dots = [PE[0] @ PE[i] / (np.linalg.norm(PE[0]) * np.linalg.norm(PE[i])) for i in range(8)]
    print("Cosine sim to position 0:", [round(d, 3) for d in dots])


# ─────────────────────────────────────────────────────────────
# SECTION 4: Tokenization
# ─────────────────────────────────────────────────────────────

def demo_tokenization():
    print("\n" + "=" * 60)
    print("SECTION 4: Tokenization (BPE via tiktoken)")
    print("=" * 60)

    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4")

        examples = [
            "Hello, how are you?",
            "Retrieval-Augmented Generation",
            "নমস্কার",           # Bengali — tokenizes less efficiently
            "def scaled_dot_product_attention(Q, K, V):",
        ]

        print(f"\n{'Text':<45} {'Tokens':>6}  {'Token IDs'}")
        print("-" * 80)
        for text in examples:
            ids = enc.encode(text)
            print(f"{repr(text):<45} {len(ids):>6}  {ids[:6]}{'...' if len(ids) > 6 else ''}")

        # Show the ~0.75 words/token ratio
        sentence = "The quick brown fox jumps over the lazy dog"
        words = len(sentence.split())
        tokens = len(enc.encode(sentence))
        print(f"\n'{sentence}'")
        print(f"Words: {words}, Tokens: {tokens}, Ratio: {tokens/words:.2f} tokens/word")
        print("(Expected ~1.33 tokens/word for English — close to the 0.75 word/token rule)")

    except ImportError:
        print("tiktoken not installed. Run: pip install tiktoken")
        print("Manually: BPE merges frequent byte pairs iteratively.")
        print("'unhappiness' → ['un', 'hap', 'pi', 'ness'] (4 tokens, not 1 word)")


# ─────────────────────────────────────────────────────────────
# SECTION 5: Sampling — Temperature, Top-p, Greedy
# ─────────────────────────────────────────────────────────────

def sample_next_token(
    logits: np.ndarray,
    temperature: float = 1.0,
    top_p: float = 1.0,
    greedy: bool = False,
) -> int:
    """
    Simulate one decoding step given raw logits over vocabulary.

    temperature=0 → near-greedy (deterministic)
    top_p=0.9     → nucleus sampling (sample from top 90% probability mass)
    greedy=True   → argmax, no sampling
    """
    if greedy:
        return int(np.argmax(logits))

    # Apply temperature
    if temperature == 0:
        return int(np.argmax(logits))

    scaled = logits / temperature
    probs = softmax(scaled)

    # Top-p (nucleus) filtering
    if top_p < 1.0:
        sorted_idx = np.argsort(probs)[::-1]
        cumulative = np.cumsum(probs[sorted_idx])
        cutoff = np.searchsorted(cumulative, top_p) + 1
        nucleus_idx = sorted_idx[:cutoff]

        mask = np.zeros_like(probs)
        mask[nucleus_idx] = probs[nucleus_idx]
        probs = mask / mask.sum()

    return int(np.random.choice(len(probs), p=probs))


def demo_sampling():
    print("\n" + "=" * 60)
    print("SECTION 5: Sampling Strategies")
    print("=" * 60)

    np.random.seed(7)
    vocab = ["cat", "dog", "car", "sun", "run"]
    logits = np.array([2.5, 2.0, 0.5, -1.0, 1.0])   # raw model output

    probs = softmax(logits)
    print(f"\nLogits: {logits}")
    print(f"Probs:  {np.round(probs, 3)}")
    print(f"Vocab:  {vocab}")

    print("\n--- Greedy decoding ---")
    tok = sample_next_token(logits, greedy=True)
    print(f"Always picks: '{vocab[tok]}'")

    print("\n--- Temperature sampling ---")
    for temp in [0.2, 1.0, 2.0]:
        counts = {}
        for _ in range(2000):
            t = sample_next_token(logits, temperature=temp)
            counts[vocab[t]] = counts.get(vocab[t], 0) + 1
        top3 = sorted(counts.items(), key=lambda x: -x[1])[:3]
        print(f"  temp={temp}: {top3}")

    print("\n--- Top-p (nucleus) sampling (temp=1.0) ---")
    for p in [0.5, 0.9, 1.0]:
        unique = set()
        for _ in range(500):
            unique.add(vocab[sample_next_token(logits, temperature=1.0, top_p=p)])
        print(f"  top_p={p}: tokens seen = {unique}")


# ─────────────────────────────────────────────────────────────
# SECTION 6: KV Cache — concept demonstration
# ─────────────────────────────────────────────────────────────

class NaiveTransformerStep:
    """
    Illustrates the FLOPs difference between cached and non-cached inference.
    In real transformers, without KV cache every new token re-encodes all
    previous tokens. With cache, only the new token needs encoding.
    """

    def compute_flops_no_cache(self, total_tokens: int, d_model: int) -> int:
        # Each attention step is O(n^2 * d_model); we do this for each new token
        return sum((i ** 2) * d_model for i in range(1, total_tokens + 1))

    def compute_flops_with_cache(self, total_tokens: int, d_model: int) -> int:
        # With KV cache, each step only attends over full history but encodes 1 token
        return sum(i * d_model for i in range(1, total_tokens + 1))


def demo_kv_cache():
    print("\n" + "=" * 60)
    print("SECTION 6: KV Cache — Why It Matters")
    print("=" * 60)

    step = NaiveTransformerStep()
    d_model = 4096

    print(f"\n{'Tokens':>8} {'No Cache FLOPs':>20} {'With Cache FLOPs':>20} {'Speedup':>10}")
    print("-" * 65)
    for n in [10, 100, 500, 1000]:
        no_cache = step.compute_flops_no_cache(n, d_model)
        with_cache = step.compute_flops_with_cache(n, d_model)
        speedup = no_cache / with_cache
        print(f"{n:>8} {no_cache:>20,} {with_cache:>20,} {speedup:>9.1f}x")

    print("\nKey insight: KV cache trades memory for compute.")
    print("Memory cost: 2 * num_layers * seq_len * d_model * bytes_per_param")
    layers, seq_len, bytes_fp16 = 32, 1000, 2
    mem_gb = 2 * layers * seq_len * d_model * bytes_fp16 / 1e9
    print(f"Example (32 layers, 1k tokens, fp16): {mem_gb:.2f} GB of KV cache")


# ─────────────────────────────────────────────────────────────
# SECTION 7: Live API — temperature & prompting (requires API key)
# ─────────────────────────────────────────────────────────────

def demo_live_api():
    """
    Calls Claude API to show temperature effect on real outputs.
    Set ANTHROPIC_API_KEY in your environment to run this section.
    """
    print("\n" + "=" * 60)
    print("SECTION 7: Live API — Temperature & Prompting")
    print("=" * 60)

    try:
        import anthropic
        import os

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        model = "claude-haiku-4-5-20251001"    # cheapest, fast for demos
        prompt = "Complete this sentence with ONE word only: The sky is"

        print(f"\nPrompt: '{prompt}'\n")

        for temp in [0.0, 1.0, 1.5]:
            responses = []
            for _ in range(3):
                msg = client.messages.create(
                    model=model,
                    max_tokens=10,
                    temperature=temp,
                    messages=[{"role": "user", "content": prompt}],
                )
                responses.append(msg.content[0].text.strip())
            print(f"  temperature={temp}: {responses}")

    except ImportError:
        print("anthropic not installed. Run: pip install anthropic")
    except Exception as e:
        print(f"API error (check ANTHROPIC_API_KEY): {e}")


# ─────────────────────────────────────────────────────────────
# SECTION 8: Fine-tuning vs Prompting — token cost estimator
# ─────────────────────────────────────────────────────────────

def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-sonnet-4-6",
) -> float:
    """
    Rough cost in USD based on public pricing (as of 2025).
    Fine-tuning cost not included here — add training compute separately.
    """
    pricing = {
        "claude-sonnet-4-6":  (3.0, 15.0),    # $/M input, $/M output
        "claude-haiku-4-5":   (0.25, 1.25),
        "gpt-4o":             (5.0, 15.0),
        "text-embedding-3-small": (0.02, 0.0),
    }
    if model not in pricing:
        raise ValueError(f"Unknown model: {model}")

    in_price, out_price = pricing[model]
    return (input_tokens * in_price + output_tokens * out_price) / 1_000_000


def demo_cost_estimator():
    print("\n" + "=" * 60)
    print("SECTION 8: Token Cost Estimator")
    print("=" * 60)

    scenarios = [
        ("Single agent turn",      2_000,   500),
        ("10-turn conversation",  20_000, 5_000),
        ("1k agent runs/day",  2_000_000, 500_000),
    ]

    print(f"\n{'Scenario':<30} {'Input':>10} {'Output':>10} {'Cost (Sonnet)':>15} {'Cost (Haiku)':>13}")
    print("-" * 82)
    for name, inp, out in scenarios:
        cost_sonnet = estimate_cost(inp, out, "claude-sonnet-4-6")
        cost_haiku  = estimate_cost(inp, out, "claude-haiku-4-5")
        print(f"{name:<30} {inp:>10,} {out:>10,} ${cost_sonnet:>13.4f} ${cost_haiku:>11.4f}")

    print("\nRule of thumb: route cheap/simple subtasks to Haiku, reserve Sonnet for reasoning.")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_attention()
    demo_multi_head()
    demo_positional_encoding()
    demo_tokenization()
    demo_sampling()
    demo_kv_cache()
    demo_cost_estimator()
    demo_live_api()   # requires ANTHROPIC_API_KEY
