# PDF Embed Chroma

A small `uv` project that extracts text from a PDF, chunks it, embeds the
chunks with a local SentenceTransformers model, and stores them in a persistent
ChromaDB collection.

## Setup

```bash
cd rag
uv sync
```

The first ingest or query can download the default embedding model
(`all-MiniLM-L6-v2`) through `sentence-transformers`.

## Embed a PDF

```bash
uv run pdf-embed-chroma ingest path/to/file.pdf
```

By default, embeddings are stored in `.chroma` under the `pdf_chunks`
collection.

Useful options:

```bash
uv run pdf-embed-chroma ingest path/to/file.pdf --reset
uv run pdf-embed-chroma ingest path/to/file.pdf --collection research_notes
uv run pdf-embed-chroma ingest path/to/file.pdf --chunk-size 1200 --chunk-overlap 200
```

## Query Stored Chunks

```bash
uv run pdf-embed-chroma query "What is the document about?"
```

Use the same `--persist-dir`, `--collection`, and `--model` values for querying
that you used while ingesting.

## Visual Lesson

Open `animation/index.html` in a browser to see a student-friendly animation of
the PDF-to-ChromaDB retrieval flow.
