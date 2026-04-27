from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


DEFAULT_COLLECTION = "pdf_chunks"
DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_PERSIST_DIR = ".chroma"


@dataclass(frozen=True)
class PdfChunk:
    id: str
    text: str
    metadata: dict[str, Any]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> Iterable[str]:
    if chunk_size < 100:
        raise ValueError("--chunk-size must be at least 100 characters")
    if chunk_overlap < 0:
        raise ValueError("--chunk-overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("--chunk-overlap must be smaller than --chunk-size")

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length:
            last_space = text.rfind(" ", start, end)
            if last_space > start + chunk_size // 2:
                end = last_space

        chunk = text[start:end].strip()
        if chunk:
            yield chunk

        if end >= text_length:
            break

        start = max(end - chunk_overlap, start + 1)


def chunk_id(pdf_path: Path, page_number: int, chunk_number: int, text: str) -> str:
    source = f"{pdf_path.resolve()}:{page_number}:{chunk_number}:{text}"
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:16]
    safe_stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", pdf_path.stem).strip("-")
    return f"{safe_stem}-p{page_number}-c{chunk_number}-{digest}"


def extract_pdf_chunks(
    pdf_path: Path,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[PdfChunk]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency pypdf. Run `uv sync` before ingesting PDFs."
        ) from exc

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if not pdf_path.is_file():
        raise SystemExit(f"Expected a PDF file, got: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    chunks: list[PdfChunk] = []

    for page_index, page in enumerate(reader.pages, start=1):
        page_text = normalize_text(page.extract_text() or "")
        if not page_text:
            continue

        for chunk_index, text in enumerate(
            split_text(page_text, chunk_size, chunk_overlap),
            start=1,
        ):
            chunks.append(
                PdfChunk(
                    id=chunk_id(pdf_path, page_index, chunk_index, text),
                    text=text,
                    metadata={
                        "source": str(pdf_path),
                        "page": page_index,
                        "chunk": chunk_index,
                    },
                )
            )

    return chunks


def batched(items: Sequence[PdfChunk], batch_size: int) -> Iterable[Sequence[PdfChunk]]:
    if batch_size < 1:
        raise ValueError("--batch-size must be at least 1")
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def get_collection(
    *,
    persist_dir: Path,
    collection_name: str,
    model_name: str,
    reset: bool = False,
):
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency chromadb or sentence-transformers. Run `uv sync` first."
        ) from exc

    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))

    if reset:
        try:
            client.delete_collection(collection_name)
        except Exception as exc:
            message = str(exc).lower()
            if "does not exist" not in message and "not found" not in message:
                raise

    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name
    )
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )


def ingest(args: argparse.Namespace) -> None:
    pdf_path = Path(args.pdf).expanduser()
    persist_dir = Path(args.persist_dir).expanduser()

    chunks = extract_pdf_chunks(
        pdf_path,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    if not chunks:
        raise SystemExit(f"No extractable text found in {pdf_path}")

    collection = get_collection(
        persist_dir=persist_dir,
        collection_name=args.collection,
        model_name=args.model,
        reset=args.reset,
    )

    for batch in batched(chunks, args.batch_size):
        collection.upsert(
            ids=[chunk.id for chunk in batch],
            documents=[chunk.text for chunk in batch],
            metadatas=[chunk.metadata for chunk in batch],
        )

    print(
        f"Indexed {len(chunks)} chunks from {pdf_path} "
        f"into collection '{args.collection}' at {persist_dir}."
    )


def query(args: argparse.Namespace) -> None:
    collection = get_collection(
        persist_dir=Path(args.persist_dir).expanduser(),
        collection_name=args.collection,
        model_name=args.model,
    )

    results = collection.query(query_texts=[args.question], n_results=args.top_k)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        print("No matching chunks found.")
        return

    for index, document in enumerate(documents, start=1):
        metadata = metadatas[index - 1] if index - 1 < len(metadatas) else {}
        distance = distances[index - 1] if index - 1 < len(distances) else None
        location = f"{metadata.get('source', 'unknown')}#page={metadata.get('page', '?')}"
        score = f" distance={distance:.4f}" if isinstance(distance, float) else ""
        print(f"\n[{index}] {location}{score}")
        print(document)


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--persist-dir",
        default=DEFAULT_PERSIST_DIR,
        help=f"Directory for ChromaDB data. Default: {DEFAULT_PERSIST_DIR}",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"Chroma collection name. Default: {DEFAULT_COLLECTION}",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"SentenceTransformers model name. Default: {DEFAULT_MODEL}",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-embed-chroma",
        description="Embed PDF text into a persistent ChromaDB collection.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Embed and store a PDF")
    add_common_options(ingest_parser)
    ingest_parser.add_argument("pdf", help="Path to the PDF file")
    ingest_parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Maximum characters per chunk. Default: 1000",
    )
    ingest_parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=150,
        help="Characters of overlap between chunks. Default: 150",
    )
    ingest_parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Chunks to upsert per ChromaDB batch. Default: 64",
    )
    ingest_parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the collection before ingesting.",
    )
    ingest_parser.set_defaults(func=ingest)

    query_parser = subparsers.add_parser("query", help="Search embedded PDF chunks")
    add_common_options(query_parser)
    query_parser.add_argument("question", help="Search question or phrase")
    query_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to return. Default: 5",
    )
    query_parser.set_defaults(func=query)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
