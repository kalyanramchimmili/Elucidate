"""
ingest.py — Load a PDF, chunk it, embed it, persist to ChromaDB
Usage: python ingest.py <path_to_pdf>
"""

import sys
import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from ingest.config import (
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    print(f"Reading PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(text)
    print(f"  Extracted {len(pages)} pages")
    return "\n".join(pages)


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP  # 2000-250
    print(f"  Split into {len(chunks)} chunks")
    return chunks


_client = None
_ef     = None

def get_client_and_ef():
    """Singleton ChromaDB client and embedding function — loaded once, reused."""
    global _client, _ef
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    if _ef is None:
        _ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
    return _client, _ef


def ingest(pdf_path: str, collection_name: str):
    """Ingest a PDF into a named ChromaDB collection."""
    if not os.path.exists(pdf_path):
        print(f"Error: File not found — {pdf_path}")
        sys.exit(1)

    text = extract_text(pdf_path)
    chunks = chunk_text(text)

    client, ef = get_client_and_ef()
    print(f"Connecting to ChromaDB at: {CHROMA_DB_PATH}")

    try:
        client.delete_collection(name=collection_name)
        print("  Cleared existing collection")
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=ef,
    )

    batch_size = 50
    total = len(chunks)
    for i in range(0, total, batch_size):
        batch = chunks[i: i + batch_size]
        ids = [f"chunk_{j}" for j in range(i, i + len(batch))]
        collection.add(documents=batch, ids=ids)
        print(f"  Ingested {min(i + batch_size, total)}/{total} chunks", end="\r")

    print(f"\nDone. {total} chunks stored in ChromaDB.")
    return collection


def initialise(pdf_path: str, collection_name: str):
    """
    Load collection from cache if exists, otherwise ingest fresh.
    Returns (collection, status) — status is 'cached' or 'ready'
    """
    client, ef = get_client_and_ef()
    existing = [c.name for c in client.list_collections()]

    if collection_name in existing:
        print(f"  Loading from cache: {collection_name}")
        collection = client.get_collection(name=collection_name, embedding_function=ef)
        return collection, "cached"
    else:
        print(f"  New PDF — ingesting: {collection_name}")
        collection = ingest(pdf_path, collection_name)
        return collection, "ready"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path_to_pdf>")
        sys.exit(1)
    collection_name = os.path.basename(sys.argv[1]).replace(" ", "_").replace(".pdf", "").lower()
    ingest(sys.argv[1], collection_name)
