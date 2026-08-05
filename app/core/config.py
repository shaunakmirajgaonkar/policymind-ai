"""
Central config for PolicyMind AI. 100% local, no cloud.
No internet access — cannot fetch real economic indicators, demographic
data, or legislative databases. All quantitative inputs (affected
population, cost estimates, historical outcome data) must be supplied by
the user from their own research. This tool computes transparent
simulations and RAG retrieval over documents the user provides — it never
fabricates economic or demographic statistics.
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR = DATA_DIR / "chroma_store"
CHROMA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'policymind.db'}"

OLLAMA_MODEL = os.getenv("PM2_OLLAMA_MODEL", "phi3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("PM2_EMBED_MODEL", "all-MiniLM-L6-v2")

API_HOST = "0.0.0.0"
API_PORT = int(os.getenv("PM2_API_PORT", "8600"))

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K_RESULTS = 5
MONTE_CARLO_TRIALS = 2000
RANDOM_STATE = 42
