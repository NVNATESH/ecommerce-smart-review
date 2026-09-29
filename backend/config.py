"""Central configuration. All tunables come from environment variables with safe defaults."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

APP_NAME = "E-Commerce Smart Review & Sentiment Engine"
APP_VERSION = "1.0.0"
API_PREFIX = "/api"

MODELS_DIR = Path(os.getenv("MODELS_DIR", str(BASE_DIR / "models")))
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
LOGS_DIR = Path(os.getenv("LOGS_DIR", str(BASE_DIR / "logs")))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Upload / input limits (all treated as untrusted input) ---
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_ROWS = int(os.getenv("MAX_ROWS", "20000"))
MAX_REVIEW_LENGTH = int(os.getenv("MAX_REVIEW_LENGTH", "5000"))
MAX_TOTAL_TEXT_LENGTH = int(os.getenv("MAX_TOTAL_TEXT_LENGTH", "2_000_000"))
MAX_PASTED_TEXT_LENGTH = int(os.getenv("MAX_PASTED_TEXT_LENGTH", "100_000"))

ALLOWED_UPLOAD_EXTENSIONS = {".csv"}

# --- CORS: only the frontend origin is allowed; override in production via env ---
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]

# --- CSV review column candidates, in priority order ---
REVIEW_COLUMNS = [
    "review",
    "review_text",
    "comment",
    "comments",
    "feedback",
    "text",
    "customer_review",
    "product_review",
]

# --- Dataset validation thresholds (spec section 14) ---
DATASET_REVIEW_COUNT_VALID = 5      # >=5 valid
DATASET_REVIEW_COUNT_WARNING = 3    # 3-4 warning, <3 reject
AVG_WORD_COUNT_GOOD = 5
AVG_WORD_COUNT_WARNING = 3

# --- Review detector thresholds (spec section 15) ---
REVIEW_PROBA_VALID = 0.80
REVIEW_PROBA_INVALID = 0.20

# --- Quality engine decision bands (spec section 28) ---
QUALITY_ACCEPT = 80
QUALITY_ACCEPT_WITH_WARNING = 60

# --- Duplicate detection (cosine similarity over char 3-5 grams) ---
NEAR_DUPLICATE_SIMILARITY = 0.55

# --- Aspect aggregation: pros/cons listing ---
# An aspect appears under Pros when positive mentions outnumber negative ones
# (and under Cons for the reverse). A single review can never create a
# "major" pro/con: lists are ranked by percentage and mention volume, so
# multi-mention aspects always rank above single-review ones.
MIN_MENTIONS_FOR_PRO_CON = 1
PRO_CON_LIST_CAP = 8

for _d in (MODELS_DIR, DATA_DIR, LOGS_DIR, DATA_DIR / "raw", DATA_DIR / "processed"):
    _d.mkdir(parents=True, exist_ok=True)
