"""
Reranking and Query Expansion / HyDE
=====================================
Two techniques that significantly improve RAG retrieval quality.

RERANKING:
  - First-pass retrieval (bi-encoder) fetches top-50 candidates fast
  - Second-pass reranker (cross-encoder) scores & re-orders to top-5
  - Cross-encoders see (query, doc) together → much more accurate
  - Cost: 2–5× latency increase

QUERY EXPANSION / HyDE (Hypothetical Document Embedding):
  - LLM generates a *hypothetical* answer to the query
  - Embed that answer and search with it instead of (or alongside) the query
  - Hypothetical answer is closer in embedding space to real relevant docs
"""

import os
import numpy as np
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


# ---------------------------------------------------------------------------
# 1. RERANKING — conceptual simulation (no paid API required)
# ---------------------------------------------------------------------------

class BiEncoderSimulator:
    """
    Fast first-pass retrieval. Encodes query and docs independently.
    Real world: sentence-transformers, OpenAI text-embedding-3-small, etc.
    Here we use random vectors to illustrate the pipeline shape.
    """

    def __init__(self, dim: int = 64, seed: int = 42):
        self.dim = dim
        self.rng = np.random.default_rng(seed)

    def embed(self, texts: List[str]) -> np.ndarray:
        # Deterministic fake embeddings keyed on text content
        vecs = []
        for t in texts:
            seed_val = sum(ord(c) for c in t) % 10000
            rng = np.random.default_rng(seed_val)
            vecs.append(rng.standard_normal(self.dim))
        return np.array(vecs)

    def retrieve(self, query: str, corpus: List[str], top_k: int = 10) -> List[Tuple[int, float]]:
        """Return (doc_index, score) sorted descending."""
        q_vec = self.embed([query])[0]
        d_vecs = self.embed(corpus)
        scores = [cosine_similarity(q_vec, d) for d in d_vecs]
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


class CrossEncoderSimulator:
    """
    Accurate second-pass reranker. Sees (query, doc) together.
    Real world: Cohere Rerank, BGE-reranker-large, ms-marco-MiniLM, etc.
    Here we simulate higher accuracy by using character-level keyword overlap.
    """

    def score(self, query: str, doc: str) -> float:
        q_terms = set(query.lower().split())
        d_terms = set(doc.lower().split())
        overlap = len(q_terms & d_terms)
        # Boost docs that have the query terms early (position bias simulation)
        early_bonus = sum(1 for t in q_terms if doc.lower().find(t) < 100) * 0.05
        return overlap / (len(q_terms) + 1e-9) + early_bonus

    def rerank(self, query: str, candidates: List[Tuple[int, str]], top_k: int = 5) -> List[Tuple[int, float]]:
        scored = [(idx, self.score(query, doc)) for idx, doc in candidates]
        return sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]


def demo_reranking():
    print("=" * 60)
    print("DEMO: Two-Stage Reranking Pipeline")
    print("=" * 60)

    corpus = [
        "Transformers use self-attention to model token relationships.",
        "The capital of France is Paris, a major European city.",
        "BERT is a bidirectional transformer pre-trained on masked LM.",
        "Attention mechanisms assign weights to input tokens dynamically.",
        "Neural networks consist of layers of weighted connections.",
        "Cross-encoders jointly encode query and document for scoring.",
        "Bi-encoders encode query and document independently for speed.",
        "Reranking improves precision by applying a costly model to fewer docs.",
        "RAG combines retrieval with generation for knowledge-grounded answers.",
        "Vector databases store embeddings for approximate nearest-neighbor search.",
        "Gradient descent minimizes loss by iteratively updating weights.",
        "Paris is famous for the Eiffel Tower and haute cuisine.",
    ]

    query = "How does reranking improve retrieval accuracy in RAG systems?"

    bi_encoder = BiEncoderSimulator()
    cross_encoder = CrossEncoderSimulator()

    # Stage 1: fast bi-encoder retrieval (top-10 from corpus)
    print(f"\nQuery: {query!r}\n")
    print("--- Stage 1: Bi-encoder (fast, top-10) ---")
    bi_results = bi_encoder.retrieve(query, corpus, top_k=10)
    for rank, (idx, score) in enumerate(bi_results, 1):
        print(f"  {rank:2d}. [{score:.3f}] {corpus[idx]}")

    # Stage 2: cross-encoder reranks the top-10 → top-5
    candidates = [(idx, corpus[idx]) for idx, _ in bi_results]
    print("\n--- Stage 2: Cross-encoder rerank (accurate, top-5) ---")
    reranked = cross_encoder.rerank(query, candidates, top_k=5)
    for rank, (idx, score) in enumerate(reranked, 1):
        print(f"  {rank:2d}. [{score:.3f}] {corpus[idx]}")

    print("\nKey insight: cross-encoder sees query+doc together → better overlap detection")


# ---------------------------------------------------------------------------
# 2. QUERY EXPANSION
#    Multiple query variants → union of retrieved docs → more recall
# ---------------------------------------------------------------------------

def expand_query(query: str) -> List[str]:
    """
    Real world: use an LLM to generate paraphrases / sub-questions.
    Here: a hand-crafted expansion for illustration.
    """
    expansions = {
        "What is RAG?": [
            "Retrieval augmented generation explanation",
            "How does retrieval augmented generation work?",
            "RAG architecture overview",
        ],
        "How does attention work in transformers?": [
            "self-attention mechanism transformer",
            "query key value attention computation",
            "multi-head attention explained",
        ],
    }
    return expansions.get(query, [query + " overview", query + " explained", query])


def demo_query_expansion():
    print("\n" + "=" * 60)
    print("DEMO: Query Expansion")
    print("=" * 60)

    corpus = [
        "RAG retrieves documents then feeds them to an LLM as context.",
        "Retrieval augmented generation grounds LLM answers in real data.",
        "Self-attention computes a weighted sum of value vectors.",
        "Multi-head attention runs several attention heads in parallel.",
        "The query, key, and value matrices are learned projections.",
        "RAG reduces hallucination by providing retrieved evidence.",
        "Transformers replaced RNNs for sequence modeling tasks.",
    ]

    query = "What is RAG?"
    bi_encoder = BiEncoderSimulator()

    print(f"\nOriginal query: {query!r}")
    variants = [query] + expand_query(query)
    print(f"Expanded to {len(variants)} queries:")
    for v in variants:
        print(f"  - {v!r}")

    # Retrieve for each variant and union results
    all_indices = set()
    for v in variants:
        results = bi_encoder.retrieve(v, corpus, top_k=3)
        all_indices.update(idx for idx, _ in results)

    print(f"\nUnion of retrieved docs ({len(all_indices)} unique):")
    for idx in sorted(all_indices):
        print(f"  [{idx}] {corpus[idx]}")

    print("\nKey insight: expansion catches docs that match paraphrases, not just exact wording")


# ---------------------------------------------------------------------------
# 3. HyDE — Hypothetical Document Embedding
#    Generate a fake answer → embed it → search with that embedding
# ---------------------------------------------------------------------------

HYPOTHETICAL_ANSWERS = {
    "What causes transformer attention to be slow at long sequences?": (
        "Transformer self-attention has O(n²) complexity because every token "
        "attends to every other token. For a sequence of length n the attention "
        "matrix is n×n, making memory and compute quadratic in sequence length."
    ),
    "How does reranking work in RAG?": (
        "In RAG reranking, a first-pass bi-encoder quickly retrieves the top-50 "
        "candidates using approximate nearest-neighbor search. A cross-encoder "
        "then scores each (query, candidate) pair jointly, producing a more "
        "accurate ranking. The top-5 reranked results are passed to the LLM."
    ),
}


def generate_hypothetical_answer(query: str) -> str:
    """
    Real world: call an LLM (e.g. GPT-4o, Claude) with a prompt like:
        'Write a short passage that would answer: {query}'
    Here: return a pre-written answer for illustration.
    """
    return HYPOTHETICAL_ANSWERS.get(
        query,
        f"A hypothetical passage that directly answers the question: {query} "
        "would explain the concept step by step, providing relevant details "
        "and examples drawn from domain knowledge.",
    )


def demo_hyde():
    print("\n" + "=" * 60)
    print("DEMO: HyDE — Hypothetical Document Embedding")
    print("=" * 60)

    corpus = [
        "Self-attention is O(n²) in sequence length due to the full attention matrix.",
        "Flash attention reduces memory by computing attention in blocks.",
        "Sparse attention patterns limit each token to attending to a subset of others.",
        "Linear attention approximates full attention in O(n) time.",
        "Long documents challenge transformers because of quadratic complexity.",
        "Retrieval augmented generation grounds model answers in retrieved evidence.",
        "Cross-encoders jointly score query-document pairs for high accuracy.",
    ]

    query = "What causes transformer attention to be slow at long sequences?"
    bi_encoder = BiEncoderSimulator()

    print(f"\nQuery: {query!r}\n")

    # Standard retrieval: embed the query itself
    standard_results = bi_encoder.retrieve(query, corpus, top_k=3)
    print("--- Standard retrieval (embed query directly) ---")
    for rank, (idx, score) in enumerate(standard_results, 1):
        print(f"  {rank}. [{score:.3f}] {corpus[idx]}")

    # HyDE retrieval: embed the hypothetical answer
    hyp_answer = generate_hypothetical_answer(query)
    print(f"\nHypothetical answer generated by LLM:\n  \"{hyp_answer[:120]}...\"\n")

    hyde_results = bi_encoder.retrieve(hyp_answer, corpus, top_k=3)
    print("--- HyDE retrieval (embed hypothetical answer) ---")
    for rank, (idx, score) in enumerate(hyde_results, 1):
        print(f"  {rank}. [{score:.3f}] {corpus[idx]}")

    print(
        "\nKey insight: the hypothetical answer contains richer vocabulary that "
        "aligns better with how real relevant docs are written."
    )


# ---------------------------------------------------------------------------
# 4. COMBINED PIPELINE: HyDE + Reranking
# ---------------------------------------------------------------------------

def demo_combined():
    print("\n" + "=" * 60)
    print("DEMO: Full Pipeline — HyDE → Bi-encoder → Cross-encoder Rerank")
    print("=" * 60)

    corpus = [
        "Self-attention is O(n²) in sequence length due to the full attention matrix.",
        "Flash attention reduces memory by computing attention in blocks.",
        "Sparse attention patterns limit each token to attending to a subset.",
        "Linear attention approximates full attention in O(n) time.",
        "Long documents challenge transformers because of quadratic complexity.",
        "RAG grounds model answers in retrieved evidence to reduce hallucination.",
        "Cross-encoders jointly score query-document pairs for high accuracy.",
        "Bi-encoders encode query and document independently for fast retrieval.",
        "Reranking applies a costly model to a small candidate set for precision.",
        "HyDE generates a hypothetical answer then embeds it for retrieval.",
    ]

    query = "What causes transformer attention to be slow at long sequences?"
    bi_encoder = BiEncoderSimulator()
    cross_encoder = CrossEncoderSimulator()

    print(f"\nQuery: {query!r}")

    # Step 1 — HyDE: generate + embed hypothetical answer
    hyp = generate_hypothetical_answer(query)
    search_text = hyp  # use the hypothetical answer as the search vector

    # Step 2 — Bi-encoder: fast first-pass (top-8)
    bi_results = bi_encoder.retrieve(search_text, corpus, top_k=8)
    print(f"\nAfter HyDE + bi-encoder (top-8 candidates): {len(bi_results)} docs")

    # Step 3 — Cross-encoder: rerank → top-3
    candidates = [(idx, corpus[idx]) for idx, _ in bi_results]
    final = cross_encoder.rerank(query, candidates, top_k=3)

    print("\nFinal top-3 after reranking:")
    for rank, (idx, score) in enumerate(final, 1):
        print(f"  {rank}. [{score:.3f}] {corpus[idx]}")

    print(
        "\nPipeline summary:\n"
        "  HyDE         → richer query representation\n"
        "  Bi-encoder   → fast candidate retrieval (O(1) per query at search time)\n"
        "  Cross-encoder→ accurate reranking over small candidate set\n"
    )


# ---------------------------------------------------------------------------
# When to use what (cheat sheet)
# ---------------------------------------------------------------------------

CHEAT_SHEET = """
╔══════════════════╦══════════════════════╦═══════════════════════════════════╗
║ Technique        ║ When to use          ║ Trade-off                         ║
╠══════════════════╬══════════════════════╬═══════════════════════════════════╣
║ Bi-encoder       ║ Always (first pass)  ║ Fast but less accurate            ║
║ Cross-encoder    ║ When precision > lat ║ 2–5× latency, much more accurate  ║
║ Query Expansion  ║ Short/ambiguous query║ More LLM calls, higher recall     ║
║ HyDE             ║ When query phrasing  ║ One LLM call per query, can       ║
║                  ║ differs from docs    ║ hallucinate irrelevant hypotheses  ║
╚══════════════════╩══════════════════════╩═══════════════════════════════════╝

Real-world libraries:
  Reranking      : cohere.rerank(), sentence-transformers CrossEncoder,
                   FlagEmbedding (BGE-reranker-v2-m3)
  Query Expansion: LangChain MultiQueryRetriever, LlamaIndex QueryTransform
  HyDE           : LangChain HypotheticalDocumentEmbedder,
                   LlamaIndex HyDEQueryTransform
"""


if __name__ == "__main__":
    demo_reranking()
    demo_query_expansion()
    demo_hyde()
    demo_combined()
    print("\n" + "=" * 60)
    print("CHEAT SHEET")
    print("=" * 60)
    print(CHEAT_SHEET)
