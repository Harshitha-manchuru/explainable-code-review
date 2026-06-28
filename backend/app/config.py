"""
Centralized application configuration.

All environment-driven settings, file paths, and model identifiers
are defined here so other modules never read os.environ directly.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_store"

PEP8_RULES_PATH = KNOWLEDGE_BASE_DIR / "pep8_rules.json"
GOOGLE_STYLE_PATH = KNOWLEDGE_BASE_DIR / "google_style_excerpts.json"
ANTI_PATTERNS_PATH = KNOWLEDGE_BASE_DIR / "anti_patterns.json"

# ---------- ChromaDB ----------
CHROMA_COLLECTION_NAME = "python_style_rules"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
RETRIEVAL_TOP_K = 3

# ---------- Gemini ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
GEMINI_TEMPERATURE = 0.2
GEMINI_MAX_OUTPUT_TOKENS = 512

# Stub mode: if no API key is present, the system falls back to a
# deterministic offline explanation generator. This lets the full
# pipeline run end-to-end without network access or billing.
USE_LLM_STUB = GEMINI_API_KEY.strip() == ""

# ---------- Faithfulness Checker ----------
NLI_MODEL_NAME = "cross-encoder/nli-deberta-v3-base"
FAITHFULNESS_ENTAILMENT_THRESHOLD = 0.5

# ---------- CORS ----------
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# ---------- Static Analysis ----------
MAX_CODE_LENGTH_CHARS = 20000
ANALYSIS_TIMEOUT_SECONDS = 15
