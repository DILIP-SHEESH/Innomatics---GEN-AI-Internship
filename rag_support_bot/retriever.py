"""
retriever.py
------------
Retrieval Layer:
  User query → Embed → ChromaDB similarity search → Top-K chunks + scores

This module sits between the user input and the LLM.
It finds the most semantically relevant chunks from our knowledge base
so the LLM can answer with grounded context instead of hallucinating.
"""

import chromadb
from embeddings import get_embedder, MODEL_SAVE_PATH
from config import CHROMA_DB_PATH, TOP_K_RESULTS, CONFIDENCE_THRESHOLD


class Retriever:
    """
    Manages the connection to ChromaDB and handles similarity search.

    Retrieval strategy:
    - Embed the user query using the SAME embedder used during ingestion
    - Query ChromaDB for top-K most similar chunks
    - Return chunks with their similarity scores
    - Score is used downstream to decide: answer vs. escalate
    """

    def __init__(self):
        # Load the pre-fitted embedder (from disk — no retraining)
        self.embedder   = get_embedder()
        self.client     = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_collection("shopeasy_support")
        print(f"🔍 Retriever ready. KB size: {self.collection.count()} chunks")

    def retrieve(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        """
        Find the most relevant chunks for a given query.

        Returns list of dicts:
        [
          {
            "text": "chunk text...",
            "score": 0.82,        # cosine similarity (0–1, higher = more relevant)
            "page": 2,
            "source": "data/shopeasy_support_kb.pdf"
          },
          ...
        ]

        ChromaDB distance → similarity:
        ChromaDB returns 'distance' with cosine space.
        distance = 1 - similarity, so similarity = 1 - distance
        """
        query_embedding = self.embedder.embed_one(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            similarity = max(0.0, 1.0 - dist)   # Convert distance → similarity
            chunks.append({
                "text"  : doc,
                "score" : round(similarity, 4),
                "page"  : meta.get("page", "?"),
                "source": meta.get("source", "?")
            })

        # Sort by score descending (ChromaDB should already do this, but explicit)
        chunks.sort(key=lambda x: x["score"], reverse=True)
        return chunks

    def retrieve_with_confidence(self, query: str) -> tuple[list[dict], str]:
        """
        Retrieve chunks AND compute an overall confidence signal.

        Returns:
        - chunks: list of retrieved chunk dicts
        - confidence_level: "HIGH" | "MEDIUM" | "LOW"

        Confidence logic:
        - HIGH  : top chunk score ≥ 0.6
        - MEDIUM: top chunk score ≥ CONFIDENCE_THRESHOLD
        - LOW   : top chunk score < CONFIDENCE_THRESHOLD (→ trigger HITL)
        """
        chunks = self.retrieve(query)

        if not chunks:
            return [], "LOW"

        top_score = chunks[0]["score"]

        if top_score >= 0.6:
            confidence = "HIGH"
        elif top_score >= CONFIDENCE_THRESHOLD:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return chunks, confidence

    def format_context(self, chunks: list[dict]) -> str:
        """
        Concatenate retrieved chunks into a single context string for the LLM prompt.
        Each chunk is labelled with its source page for traceability.
        """
        if not chunks:
            return "No relevant information found in the knowledge base."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i} | Page {chunk['page']} | Relevance: {chunk['score']:.2f}]\n"
                f"{chunk['text']}"
            )
        return "\n\n---\n\n".join(context_parts)


# ── Singleton for reuse across modules ────────────────────────────────────────
_retriever_instance = None

def get_retriever() -> Retriever:
    """Returns a shared Retriever instance (lazy init, reused across calls)."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance


if __name__ == "__main__":
    retriever = Retriever()

    test_queries = [
        "How do I track my order?",
        "I was charged twice",
        "What is the return policy?",
        "My account was hacked",
        "Do you deliver to other countries?",
    ]

    for q in test_queries:
        chunks, confidence = retriever.retrieve_with_confidence(q)
        print(f"\nQuery  : {q}")
        print(f"Conf   : {confidence} (top score: {chunks[0]['score'] if chunks else 0})")
        print(f"Top doc: {chunks[0]['text'][:100] if chunks else 'None'}...")
