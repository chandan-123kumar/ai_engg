# RAG Fundamentals — Interview Guide

## RAG Pipeline Components

```
Documents → Chunking → Embedding → Vector Store
                                        ↓
User Query → Embed Query → Similarity Search → Retrieved Chunks
                                                      ↓
                                   LLM + Chunks + Query → Answer
```

## Chunking Strategies

| Strategy | How | Best for |
|---|---|---|
| Fixed-size | Split every N tokens with overlap | Simple docs, fast |
| Sentence-based | Split on sentence boundaries | Prose, articles |
| Recursive | Try `\n\n`, `\n`, ` ` in order | Code, mixed content |
| Semantic | Embed + split on topic shifts | Long docs with sections |
| Document-aware | Use headers, tables as boundaries | PDFs, HTML |

**Overlap**: 10–20% overlap between chunks prevents answer from being split across boundaries.

**Chunk size trade-off**:
- Smaller chunks → more precise retrieval, less noise
- Larger chunks → more context per chunk, fewer retrievals needed
- Typical sweet spot: 256–512 tokens

## Embedding Models

| Model | Dims | Context | Notes |
|---|---|---|---|
| text-embedding-3-small | 1536 | 8191 | Best cost/perf for most tasks |
| text-embedding-3-large | 3072 | 8191 | Higher accuracy, 2× cost |
| BGE-M3 | 1024 | 8192 | Open source, multilingual |
| Cohere embed-v3 | 1024 | 512 | Strong for retrieval tasks |

**Distance metrics**:
- Cosine similarity: most common, angle between vectors (scale-invariant)
- Dot product: faster, but scale-sensitive
- L2/Euclidean: good for structured data

## Vector Stores

| Store | Type | Best for |
|---|---|---|
| Pinecone | Managed | Production, low ops overhead |
| Weaviate | Self-hosted/cloud | Rich filtering, multi-modal |
| Qdrant | Self-hosted/cloud | High performance, open source |
| ChromaDB | Local | Development, prototyping |
| pgvector | Postgres extension | Already using Postgres |
| FAISS | Library | Research, no server needed |

## Retrieval Techniques

### Sparse vs Dense vs Hybrid
- **Dense**: embedding similarity (semantic meaning)
- **Sparse**: BM25/TF-IDF keyword matching (exact terms)
- **Hybrid**: combine both with RRF (Reciprocal Rank Fusion) TODO
- Hybrid consistently outperforms either alone by 5–15%

```python
# Reciprocal Rank Fusion
def rrf(dense_ranks, sparse_ranks, k=60):
    scores = {}
    for rank, doc in enumerate(dense_ranks):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank)
    for rank, doc in enumerate(sparse_ranks):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)
```

### Reranking
- First-pass retrieval gets top-50, reranker scores top-5
- Cross-encoder models (Cohere Rerank, BGE-reranker) much more accurate than bi-encoders
- Trade-off: 2–5× latency increase

### Query Expansion / HyDE //TODO
- **HyDE** (Hypothetical Document Embedding): ask LLM to write a hypothetical answer, embed that, use as query
- Works well when user query is short/vague

```python
hypo_doc = llm.invoke("Write a passage that answers: " + user_query)
embedding = embed(hypo_doc)
results = vector_store.search(embedding)
```

### Multi-Query Retrieval
- Generate N paraphrases of the query, retrieve for each, deduplicate
- Covers different angles of the question

### Parent-Child Chunking
- Index small child chunks for precision retrieval
- Return larger parent chunks to LLM for more context
- Good balance of retrieval precision + answer quality

## Advanced RAG Patterns

### RAG-Fusion
1. Generate multiple queries
2. Retrieve for each
3. Fuse with RRF
4. Generate answer
------------------------------------
### Corrective RAG (CRAG)
- Evaluate retrieved docs for relevance
- If poor, trigger web search fallback
- Re-evaluate before generating

### Self-RAG
- LLM decides WHEN to retrieve (not every turn)
- Generates retrieval tokens: `[Retrieve]`, `[NoRetrieve]`
- More efficient for conversational agents

### Agentic RAG
- Agent has retri\eval as one of many tools
- Decides search strategy, can do multi-hop retrieval
- Example: retrieve → identify gap → retrieve again with refined query

## Common Interview Questions

**Q: How do you evaluate a RAG pipeline?**
A: Split into retrieval and generation metrics.
- **Retrieval**: Recall@K (did the right chunk get retrieved?), MRR, NDCG
- **Generation**: Faithfulness (answer grounded in context?), Answer Relevance, Context Precision
- Tools: RAGAS framework automates this with LLM-as-judge

**Q: RAG vs Fine-tuning — when to use which?**
A: RAG for dynamic/updated knowledge, private docs, or when you need citations. Fine-tuning for style/format, domain-specific reasoning patterns, or speed (no retrieval step). They're complementary: fine-tune on reasoning style, use RAG for knowledge.

**Q: How do you handle questions that need multi-hop reasoning?**
A: Multi-hop RAG: retrieve → extract entities → retrieve again with those entities. Or use an agent that explicitly plans retrieval steps. LlamaIndex's sub-question engine decomposes questions automatically.

**Q: What's the "lost in the middle" problem?**
A: LLMs attend best to content at the beginning and end of context. Relevant retrieved chunks placed in the middle of a long prompt get underweighted. Solution: put most relevant chunks first/last, or use reranking to control placement.
