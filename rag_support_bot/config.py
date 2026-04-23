"""
config.py
---------
Central configuration loader.
All other modules import from here — never hardcode values elsewhere.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM
GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")
LLM_MODEL           = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# Embeddings
EMBEDDING_MODEL     = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# RAG tuning
CHUNK_SIZE          = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP       = int(os.getenv("CHUNK_OVERLAP", 50))
TOP_K_RESULTS       = int(os.getenv("TOP_K_RESULTS", 4))

# HITL threshold — retrieval score below this triggers escalation
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.35))

# File paths
PDF_PATH            = os.getenv("PDF_PATH", "data/shopeasy_support_kb.pdf")
CHROMA_DB_PATH      = os.getenv("CHROMA_DB_PATH", "data/chroma_db")

# Keywords that always trigger human escalation regardless of confidence
ESCALATION_KEYWORDS = [
    "fraud", "hacked", "scam", "unauthorized", "legal",
    "police", "lawsuit", "charged twice", "duplicate charge",
    "account compromised", "stolen", "threatening"
]