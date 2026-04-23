"""
ingest.py
---------
Document Ingestion Pipeline:
  PDF file → Load → Clean → Chunk → Embed → Store in ChromaDB

Run this ONCE before starting the bot.
Re-run only if the knowledge base PDF changes.
"""

import os
import shutil
import pypdf
import chromadb

from embeddings import get_embedder
from config import (
    PDF_PATH, CHROMA_DB_PATH,
    CHUNK_SIZE, CHUNK_OVERLAP
)


def load_pdf(path: str) -> list[str]:
    """Extract text from each page of a PDF. Returns list of page strings."""
    print(f"📄 Loading PDF: {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = pypdf.PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    pages = [p.strip() for p in pages if p.strip()]
    print(f"   ✅ Loaded {len(pages)} pages")
    return pages


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Sliding window character-level chunker with overlap.
    Overlap ensures context is preserved across chunk boundaries.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def chunk_documents(pages: list[str]) -> list[dict]:
    """
    Chunk all pages and attach metadata (page num, source file).
    Metadata is stored in ChromaDB for source attribution in responses.
    """
    print(f"✂️  Chunking (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    all_chunks = []
    for page_num, page_text in enumerate(pages):
        for chunk in chunk_text(page_text, CHUNK_SIZE, CHUNK_OVERLAP):
            all_chunks.append({
                "text": chunk,
                "page": page_num + 1,
                "source": PDF_PATH
            })
    print(f"   ✅ Created {len(all_chunks)} chunks")
    return all_chunks


def build_vector_store(chunks: list[dict], reset: bool = False):
    """
    Embed all chunks and persist them in ChromaDB.

    ChromaDB stores:
    - documents : raw text of each chunk
    - embeddings: float32 vectors (from TF-IDF + SVD)
    - metadatas : page number, source file
    - ids       : unique string IDs
    """
    if reset and os.path.exists(CHROMA_DB_PATH):
        print(f"🗑️  Resetting existing ChromaDB at {CHROMA_DB_PATH}")
        shutil.rmtree(CHROMA_DB_PATH)

    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    corpus = [c["text"] for c in chunks]
    print(f"🔢 Fitting embedder on {len(corpus)} chunks...")
    embedder = get_embedder(corpus=corpus, force_refit=True)

    print("🔢 Generating embeddings...")
    embeddings = embedder.embed_batch(corpus)

    print("💾 Storing in ChromaDB...")
    client     = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(
        name="shopeasy_support",
        metadata={"hnsw:space": "cosine"}
    )

    collection.add(
        documents=[c["text"] for c in chunks],
        embeddings=embeddings,
        metadatas=[{"page": c["page"], "source": c["source"]} for c in chunks],
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    count = collection.count()
    print(f"   ✅ {count} vectors stored in ChromaDB at: {CHROMA_DB_PATH}")
    return client, collection


def load_vector_store():
    """Load an existing ChromaDB collection without re-embedding."""
    client     = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection("shopeasy_support")
    return client, collection


def run_ingestion(reset: bool = False):
    """Orchestrates the full PDF → ChromaDB ingestion pipeline."""
    print("\n" + "="*50)
    print("  RAG INGESTION PIPELINE")
    print("="*50)

    if not reset and os.path.exists(CHROMA_DB_PATH):
        print("⚡ ChromaDB already exists. Loading existing store...")
        client, collection = load_vector_store()
        print(f"   📦 {collection.count()} vectors ready.\n")
        return client, collection

    pages  = load_pdf(PDF_PATH)
    chunks = chunk_documents(pages)
    client, collection = build_vector_store(chunks, reset=reset)

    print("\n✅ Ingestion complete! Knowledge base is ready.\n")
    return client, collection


if __name__ == "__main__":
    run_ingestion(reset=True)
