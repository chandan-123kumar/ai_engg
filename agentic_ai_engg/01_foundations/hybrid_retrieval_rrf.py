"""
Sparse vs Dense vs Hybrid Retrieval with RRF
=============================================
Run: pip install numpy scikit-learn sentence-transformers
Then: python hybrid_retrieval_rrf.py
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Sample corpus ──────────────────────────────────────────────────────────────
DOCS = [
    "The quick brown fox jumps over the lazy dog",
    "Machine learning models require large datasets for training",
    "Neural networks are inspired by the human brain structure",
    "The fox was very quick and jumped high",
    "Deep learning is a subset of machine learning techniques",
    "Dogs and foxes are both members of the canine family",
    "Transformer architectures revolutionized natural language processing",
    "The lazy cat slept all day next to the dog",
]

QUERY = "quick fox jumping"


# ── 1. SPARSE RETRIEVAL — TF-IDF (keyword matching) ───────────────────────────
#
#  Manual walkthrough with a tiny 3-doc corpus so every number is visible.
#
#  CORPUS (3 docs, 1 query):
#    = "cat sat oD0 n mat"
#    D1 = "dog sat on log"
#    D2 = "cat chased dog"
#    Q  = "cat sat"
#
#  ── STEP 1: Tokenise & build vocabulary ──────────────────────────────────────
#   vocab = {cat, sat, on, mat, dog, log, chased}   (7 unique terms)
#
#  ── STEP 2: Term Frequency (TF) ──────────────────────────────────────────────
#   TF(term, doc) = count(term in doc) / total_terms_in_doc
#
#             cat   sat   on    mat   dog   log   chased
#   D0  =  [ 1/4,  1/4,  1/4,  1/4,  0,    0,    0    ]
#   D1  =  [  0,   1/4,  1/4,  0,    1/4,  1/4,  0    ]
#   D2  =  [ 1/3,   0,    0,   0,    1/3,  0,    1/3  ]
#
#  ── STEP 3: Inverse Document Frequency (IDF) ─────────────────────────────────
#   IDF(term) = log( N / df(term) )   where N = total docs, df = docs containing term
#
#   N = 3
#   df(cat)    = 2  → IDF = log(3/2) = 0.405
#   df(sat)    = 2  → IDF = log(3/2) = 0.405
#   df(on)     = 2  → IDF = log(3/2) = 0.405
#   df(mat)    = 1  → IDF = log(3/1) = 1.099
#   df(dog)    = 2  → IDF = log(3/2) = 0.405
#   df(log)    = 1  → IDF = log(3/1) = 1.099
#   df(chased) = 1  → IDF = log(3/1) = 1.099
#
#   Rare terms (mat, log, chased) get higher IDF → more discriminative.
#   Common terms (sat, on) get lower IDF → less useful for distinguishing docs.
#
#  ── STEP 4: TF-IDF vector = TF × IDF ────────────────────────────────────────
#             cat    sat    on     mat    dog    log    chased
#   D0  =  [0.101, 0.101, 0.101, 0.275,  0,     0,     0    ]
#   D1  =  [ 0,   0.101, 0.101,  0,    0.101, 0.275,   0    ]
#   D2  =  [0.135,  0,    0,     0,    0.135,  0,     0.366 ]
#
#  ── STEP 5: Query vector ─────────────────────────────────────────────────────
#   Q = "cat sat"
#   TF(cat,Q)=1/2, TF(sat,Q)=1/2
#   Q_vec = [1/2*0.405, 1/2*0.405, 0, 0, 0, 0, 0]
#         = [0.203, 0.203, 0, 0, 0, 0, 0]
#
#  ── STEP 6: Cosine Similarity ─────────────────────────────────────────────────
#   cos(Q, D) = (Q · D) / (|Q| × |D|)
#
#   Q · D0 = 0.203*0.101 + 0.203*0.101 = 0.041   → both "cat" and "sat" match
#   Q · D1 = 0    *  0   + 0.203*0.101 = 0.020   → only "sat" matches
#   Q · D2 = 0.203*0.135 + 0    *  0   = 0.027   → only "cat" matches
#
#   ── STEP 6b: Length-normalising (why we divide) ──────────────────────────────
#   Problem: a 100-word doc has larger raw TF values than a 4-word doc just
#   because it's longer. The dot product Q·D would be huge for long docs even if
#   they're no more relevant. We need to remove the effect of document length.
#
#   Fix: divide by the Euclidean length (L2 norm) of each vector.
#   |V| = √( v1² + v2² + v3² + ... )
#
#   |Q|  = √(0.203² + 0.203²)                         = √0.082  ≈ 0.287
#   |D0| = √(0.101² + 0.101² + 0.101² + 0.275²)       = √0.106  ≈ 0.326
#   |D1| = √(0.101² + 0.101² + 0.101² + 0.275²)       = √0.106  ≈ 0.326
#   |D2| = √(0.135² + 0.135² + 0.366²)                = √0.171  ≈ 0.414
#
#   cos(Q, D0) = 0.041 / (0.287 × 0.326) = 0.041 / 0.094 ≈ 0.71  ← HIGHEST
#   cos(Q, D1) = 0.020 / (0.287 × 0.326) = 0.020 / 0.094 ≈ 0.36
#   cos(Q, D2) = 0.027 / (0.287 × 0.414) = 0.027 / 0.119 ≈ 0.38
#
#   Geometrically: you're measuring the ANGLE between two vectors, not their
#   raw magnitude. Two vectors pointing in the same direction score 1.0
#   regardless of how long they are.
#
#   → D0 ranks first. Makes sense: it contains both "cat" AND "sat".
#
#  ── WHY IT'S CALLED "SPARSE" ─────────────────────────────────────────────────
#   Each doc becomes a vector with length = vocab size (thousands in real corpora).
#   Most entries are 0 (a doc only uses a tiny fraction of all words).
#   → The matrix is sparse. No semantic understanding — only exact word overlap.
#
#  Now watch sklearn reproduce exactly this ranking on the tiny corpus:

def tfidf_manual_demo() -> None:
    mini_docs  = ["cat sat on mat", "dog sat on log", "cat chased dog"]
    mini_query = "man cam"

    vectorizer = TfidfVectorizer()
    doc_matrix = vectorizer.fit_transform(mini_docs)
    print("Vocabulary:", doc_matrix)
    query_vec  = vectorizer.transform([mini_query])
    print("Query vector:", query_vec)
    scores     = cosine_similarity(query_vec, doc_matrix).flatten()

    print("\n── TF-IDF Manual Demo (3 docs) ─────────────────────────────────")
    print(f"  Query : '{mini_query}'")
    print(f"\n  Vocabulary (index → term):")
    print(f"    (total vocab : {(vectorizer.vocabulary_)})")
    for term, idx in sorted(vectorizer.vocabulary_.items(), key=lambda x: x[1]):
        print(f"    {idx}: {term}")

    print(f"\n  TF-IDF matrix (rows=docs, cols=vocab):")
    for i, row in enumerate(doc_matrix.toarray()):
        nonzero = {vectorizer.get_feature_names_out()[j]: f"{v:.3f}"
                   for j, v in enumerate(row) if v > 0}
        print(f"    D{i} '{mini_docs[i]}' → {nonzero}")

    print(f"\n  Cosine similarity with query:")
    for i, s in enumerate(scores):
        print(f"    D{i} '{mini_docs[i]}' → {s:.4f}")

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    print(f"\n  Ranking: {[f'D{i}' for i, _ in ranked]}")
    print("  (D0 wins — it contains both 'cat' AND 'sat')")


def sparse_search(query: str, docs: list[str], top_k: int = 5) -> list[tuple[int, float]]:
    """TF-IDF sparse retrieval — exact keyword overlap drives the score."""
    vectorizer = TfidfVectorizer()
    doc_matrix = vectorizer.fit_transform(docs)
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, doc_matrix).flatten()
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


# ── 2. DENSE RETRIEVAL — Semantic embeddings ───────────────────────────────────
def dense_search(query: str, docs: list[str], top_k: int = 5) -> list[tuple[int, float]]:
    """
    Uses sentence-transformers for semantic similarity.
    Falls back to a simple TF-IDF character n-gram as a demo if not installed.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        doc_embeddings = model.encode(docs)
        query_embedding = model.encode([query])
        scores = cosine_similarity(query_embedding, doc_embeddings).flatten()
        print("  [using sentence-transformers embeddings]")
    except ImportError:
        # Fallback: character n-gram TF-IDF approximates semantic grouping poorly
        # but lets the script run without GPU/model download
        print("  [sentence-transformers not found — using char n-gram TF-IDF fallback]")
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4))
        doc_matrix = vectorizer.fit_transform(docs)
        query_vec = vectorizer.transform([query])
        scores = cosine_similarity(query_vec, doc_matrix).flatten()

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


# ── 3. RRF — Reciprocal Rank Fusion ───────────────────────────────────────────
def reciprocal_rank_fusion(
    *ranked_lists: list[tuple[int, float]],
    k: int = 60,
) -> list[tuple[int, float]]:
    """
    RRF formula: score(doc) = Σ  1 / (k + rank)
                               over all result lists

    k=60 is the standard default from the original RRF paper (Cormack 2009).
    Higher k smooths rank differences; lower k amplifies top-rank dominance.
    """
    rrf_scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, (doc_id, _score) in enumerate(ranked, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)


# ── 4. Run & compare ──────────────────────────────────────────────────────────
def print_results(label: str, results: list[tuple[int, float]], docs: list[str]) -> None:
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    for rank, (doc_id, score) in enumerate(results, start=1):
        print(f"  {rank}. [score={score:.4f}] {docs[doc_id]}")


if __name__ == "__main__":
    # ── Manual TF-IDF walkthrough first ───────────────────────────────────────
    tfidf_manual_demo()

    print(f"\n\n── Now running on the full corpus with query: '{QUERY}' ──────────")
    print(f"\nQuery: '{QUERY}'\n")

    print("Running sparse search  (TF-IDF)...")
    sparse_results = sparse_search(QUERY, DOCS)

    print("Running dense search   (embeddings)...")
    dense_results = dense_search(QUERY, DOCS)

    print("Running hybrid search  (RRF fusion)...")
    hybrid_results = reciprocal_rank_fusion(sparse_results, dense_results)

    print_results("SPARSE  — TF-IDF (exact keyword overlap)", sparse_results, DOCS)
    print_results("DENSE   — Semantic embeddings (meaning)", dense_results, DOCS)
    print_results("HYBRID  — RRF fusion of both lists", hybrid_results, DOCS)

    print("\n\n── Why hybrid wins ─────────────────────────────────────────────")
    print("""
  Sparse catches exact matches  → "quick", "fox" score high on doc 0 & 3
  Dense catches semantics       → "jumping" ~ "jumps" even without overlap
  RRF merges the ranked lists   → docs that appear high in *either* list
                                   get a strong combined score

  RRF formula: score = Σ 1/(k + rank_i)   [k=60, Cormack 2009]

  Key insight: RRF doesn't care about raw scores — only about rank positions.
  This makes it robust to score-scale differences between sparse & dense.
    """)
