"""
embeddings.py
-------------
Custom TF-IDF based embedding engine.

WHY NOT sentence-transformers here?
- sentence-transformers requires PyTorch which has environment constraints
- For a FAQ-style support KB, TF-IDF with SVD (LSA) is highly effective
- Deterministic, fast, zero API cost, fully explainable
- In production you'd swap this for OpenAI/Cohere embeddings

Design:
  1. Fit a TF-IDF vectorizer on all document chunks
  2. Apply TruncatedSVD (Latent Semantic Analysis) to reduce to 384 dims
  3. Use cosine similarity for retrieval
  4. Save/load model so we don't refit on every query
"""

import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

EMBEDDING_DIM = 384
MODEL_SAVE_PATH = "data/embedding_model.pkl"


class TFIDFEmbedder:
    """
    Lightweight local embedder using TF-IDF + LSA (Latent Semantic Analysis).
    
    Supports:
    - fit(corpus): Train on a list of text strings
    - embed(texts): Return normalized embedding vectors
    - save() / load(): Persist the fitted model
    """

    def __init__(self, n_components: int = EMBEDDING_DIM):
        self.n_components = n_components
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),       # Unigrams + bigrams
            sublinear_tf=True,         # Log normalization for TF
            strip_accents='unicode',
            analyzer='word',
            token_pattern=r'\w{2,}',  # Min 2-char words
            min_df=1
        )
        self.svd = TruncatedSVD(n_components=min(n_components, 100), random_state=42)
        self.fitted = False

    def fit(self, corpus: list[str]):
        """Train TF-IDF + SVD on the full corpus of document chunks."""
        print(f"   🔢 Fitting TF-IDF on {len(corpus)} texts...")
        tfidf_matrix = self.vectorizer.fit_transform(corpus)

        # Cap SVD components to min(n_samples-1, n_features-1, n_components)
        max_components = min(tfidf_matrix.shape[0] - 1,
                             tfidf_matrix.shape[1] - 1,
                             self.n_components)
        self.svd.n_components = max_components

        print(f"   🔢 Applying SVD (components={max_components})...")
        self.svd.fit(tfidf_matrix)
        self.fitted = True
        print(f"   ✅ Embedder fitted. Variance explained: "
              f"{self.svd.explained_variance_ratio_.sum():.2%}")

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts → normalized float32 matrix."""
        if not self.fitted:
            raise RuntimeError("Embedder not fitted yet. Call fit() first.")
        tfidf = self.vectorizer.transform(texts)
        reduced = self.svd.transform(tfidf)
        # L2 normalize so cosine similarity = dot product
        return normalize(reduced, norm='l2').astype(np.float32)

    def embed_one(self, text: str) -> list[float]:
        """Embed a single string → flat list (for ChromaDB)."""
        return self.embed([text])[0].tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of strings → list of flat lists (for ChromaDB)."""
        return self.embed(texts).tolist()

    def save(self, path: str = MODEL_SAVE_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({'vectorizer': self.vectorizer,
                         'svd': self.svd,
                         'fitted': self.fitted}, f)
        print(f"   💾 Embedder saved to {path}")

    def load(self, path: str = MODEL_SAVE_PATH):
        with open(path, 'rb') as f:
            state = pickle.load(f)
        self.vectorizer = state['vectorizer']
        self.svd        = state['svd']
        self.fitted     = state['fitted']
        print(f"   ✅ Embedder loaded from {path}")
        return self


def get_embedder(corpus: list[str] = None, force_refit: bool = False) -> TFIDFEmbedder:
    """
    Smart loader:
    - If model exists and not force_refit → load from disk
    - Else fit on provided corpus and save
    """
    embedder = TFIDFEmbedder()

    if not force_refit and os.path.exists(MODEL_SAVE_PATH):
        embedder.load(MODEL_SAVE_PATH)
    elif corpus:
        embedder.fit(corpus)
        embedder.save(MODEL_SAVE_PATH)
    else:
        raise ValueError("No saved model found and no corpus provided to fit on.")

    return embedder


if __name__ == "__main__":
    # Quick test
    corpus = [
        "How do I track my order on ShopEasy?",
        "What is the return policy for electronics?",
        "I was charged twice for my order.",
        "How do I reset my account password?",
    ]
    emb = TFIDFEmbedder()
    emb.fit(corpus)

    query_vec = emb.embed(["refund for duplicate payment"])
    doc_vecs  = emb.embed(corpus)

    # Cosine similarities (dot product since L2-normalized)
    scores = doc_vecs @ query_vec.T
    for i, (doc, score) in enumerate(zip(corpus, scores)):
        print(f"  [{score[0]:.3f}] {doc}")
