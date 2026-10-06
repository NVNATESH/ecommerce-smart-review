# E-Commerce Smart Review & Sentiment Engine

Transform customer feedback into explainable product intelligence.

A production-oriented full-stack application that analyzes customer reviews (pasted text or CSV upload) and turns them into explainable product intelligence: sentiment classification with confidence, aspect-based sentiment analysis, dataset quality scoring, duplicate & near-duplicate detection, suspicious-review signals, model evaluation and sanitized exports — presented in a premium dark 3D dashboard.

> This tool produces data-derived customer-feedback intelligence. It does **not** make purchasing decisions on your behalf, and it never claims to prove a review is fake.

---

## Screenshots

_Screenshots section — add captures of the landing page (3D hero), dashboard overview, aspect intelligence heatmap/3D chart, quality radar, suspicious reviews table and review inspector modal._

## Architecture

```
                USER
                 │
                 ▼
          NEXT.JS FRONTEND  (Next.js 15 · App Router · TypeScript · Tailwind · R3F)
                 │  REST / JSON
                 ▼
              FASTAPI  (thin routes)
                 │
   ┌─────────────┼──────────────────┐
   ▼             ▼                  ▼
INPUT LAYER   NLP ENGINES        ML ENGINES
file parser   preprocessing      sentiment model
text parser   aspect engine      review detector
validation    relevance          confidence + explainability
   └─────────────┼──────────────────┘
                 ▼
          QUALITY ENGINE ──► AGGREGATION ENGINE ──► ANALYTICS RESULT
                 │
                 ▼
      NEXT.JS DASHBOARD (Overview · Sentiment · Aspects · Quality ·
      Suspicious · Review Inspector · Model Performance · Data Explorer · Exports)
```

Key architectural rule: **the browser handles presentation and interaction while FastAPI handles the expensive NLP/ML work.** Routes stay thin (`Route → Service → NLP/ML Engine → Response Schema`), models load once at startup into a `ModelManager`, and large analyses run as background jobs with progress polling.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), React, TypeScript (strict), Tailwind CSS, Framer Motion, React Three Fiber + drei (lazy-loaded), Recharts, Lucide, Zustand |
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, python-multipart |
| NLP | NLTK (tokenization, stopwords, WordNet lemmatization) |
| ML | scikit-learn: TF-IDF + Multinomial Naive Bayes, Logistic Regression, CalibratedClassifierCV |
| Storage | joblib/pickle model artifacts + `metadata.json`; in-memory analysis store (DB-ready interface) |

## Features

- **Input methods** — paste reviews (line/paragraph separated) or drag-and-drop CSV upload with automatic review-column detection (`review`, `review_text`, `comment`, `comments`, `feedback`, `text`, `customer_review`, `product_review`).
- **Intelligent validation** — empty / whitespace / emoji-only / URL-only / number-only / symbol-only inputs each map to a stable error code (`EMPTY_INPUT`, `EMOJI_ONLY`, `URL_ONLY`, …). Malformed CSVs and missing review columns return the detected columns.
- **Review detector** — TF-IDF char n-grams + Logistic Regression, `Review` vs `Not Review`, with `VALID` (>80%), `INVALID` (<20%) and `UNCERTAIN` (in between). Uncertain data is never silently forced either way.
- **Product relevance** — graded signal from aspect presence, opinion indicators, contextual product vocabulary and detector probability. A review is never rejected merely for containing unrelated words.
- **Preprocessing** — HTML/URL removal, emoji normalization, repeated-character collapse (letters only — `5000mAh`, `120Hz`, `₹20000` survive), stopword handling with negation preserved (`not good` → `not_good`), lemmatization. Three forms per review: `original_text`, `normalized_text`, `model_text`.
- **Sentiment** — Positive / Negative / Neutral (+ **Mixed** for contradictory reviews like "Battery is amazing but the camera is disappointing"), with per-class probabilities and confidence (model certainty — never presented as guaranteed correctness).
- **Aspect-based sentiment analysis** — 18 aspect categories with synonym normalization (`battery backup` → Battery, `screen` → Display). Clause-level polarity so "battery is excellent but the camera is terrible" yields Battery→Positive, Camera→Negative.
- **Pros / cons / most-discussed features** — aggregated across mentions; a single review can never create a major pro or con.
- **Duplicate detection** — exact (hash) + near-duplicate (TF-IDF cosine over char n-grams). Records are flagged, never silently deleted; audit info is kept.
- **Suspicious review detection** — heuristic score 0–100 with reasons (all-caps, excessive punctuation, repeated words/characters, promotional language, short spam, duplicates). Reported as *suspicious* — never as proven fake.
- **Data quality engine** — transparent weighted components (review detection, opinion density, feature density, length, language quality, diversity, minus duplicate & uncertainty penalties) → `quality_score` and `ACCEPT` / `ACCEPT WITH WARNING` / `REJECT` with reasons.
- **Model evaluation** — Accuracy, Precision, Recall, Macro F1, Weighted F1 per candidate; **macro F1 is the model-selection metric**; stratified split, no leakage; confusion matrices exposed via `/api/models`.
- **Explainability** — top contributing TF-IDF features per prediction (non-causal wording: "these model features contributed strongly to the classification").
- **Async CSV processing** — upload → job → progress stages ("Detecting reviews…", "Running sentiment model…", …) via `GET /api/analysis/{id}/status`. No Celery/Redis needed.
- **Premium UI** — dark glassmorphism, subtle glow, animated borders, lazy-loaded procedural 3D hero (no external assets) and a meaningful rotatable 3D aspect chart (X: aspect, Y: sentiment score, Z: mentions).
- **Stored products (persistent)** — every analysis can be saved under a product name; feedback reviews are stored on disk (`backend/data/products/`) and survive server restarts. Build a review history per product over time.
- **Add reviews anytime** — paste new customer feedback into a stored product and the **full analysis re-runs automatically** on the combined dataset (verdict, aspects, quality all update).
- **Ask the Reviews (Q&A)** — type any question ("how is the camera?", "any delivery issues?") and the engine answers with aspect-routed evidence and real review quotes. Aspect routing + TF-IDF retrieval + template answer synthesis — no external LLM/API, fully offline.
- **Review Trust Score** — one transparent gauge (valid-review ratio, suspicious rate, duplicate rate, volume, quality) telling you **how much the dataset's verdict can be trusted**, with the component breakdown shown in the UI.
- **Compare Products** — select 2–4 stored products for a side-by-side radar overlay and per-aspect table with qualitative ratings (**Best / Excellent / Good / Average / Poor / Worst**) derived from each aspect's sentiment mix.
- **Emotion Mix** — lexicon-based emotion signals (Joy, Anger, Sadness, Fear, Love) visualized as a radar chart on the dashboard.
- **Evidence-backed Pros/Cons** — every pro/con entry carries up to 2 real review quotes as supporting evidence.
- **Emoji sentiment signals** — common emojis (😍 👍 vs 😡 👎 💔) are weighted polarity features, so reviews that express feeling through emojis are still understood.

## Folder Structure

```
ecommerce-smart-review/
├── frontend/
│   ├── app/                  # App Router pages (landing, dashboard, analysis,
│   │                         # products, compare, aspects, quality, suspicious,
│   │                         # reviews, models, exports)
│   ├── components/           # layout/ charts/ 3d/ reviews/ aspects/ upload/ ui/
│   ├── hooks/                # useAnalysis
│   ├── lib/                  # api.ts (central API layer), types.ts, utils.ts, store.ts
│   ├── public/               # sample_reviews.csv
│   └── package.json · tsconfig.json · tailwind.config.ts · next.config.ts
├── backend/
│   ├── main.py               # app factory, lifespan model loading, CORS, logging
│   ├── config.py             # env-driven configuration
│   ├── api/routes/           # health · upload · analysis · ask · products ·
│   │                         # compare · reviews · models · export
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # input, preprocessing, review detector, sentiment,
│   │                         # aspect, quality, suspicious, duplicate, aggregation,
│   │                         # export, ask (Q&A), product store (persistent),
│   │                         # analysis pipeline + store
│   ├── nlp/                  # preprocessing, tokenizer, aspect_engine, keyword_extractor,
│   │                         # emotions
│   ├── ml/                   # sentiment_model, review_detector, confidence,
│   │                         # explainability, model_manager
│   ├── validation/           # input_validator, review_validator, schema_validator
│   ├── quality/              # quality_engine
│   ├── security/             # file_security (upload validation, CSV sanitization)
│   ├── models/               # *.pkl artifacts + metadata.json (generated)
│   ├── data/                 # raw/ processed/ (training CSVs), real/ (dataset splits),
│   │                         # products/ (stored product feedback), sample_reviews.csv
│   ├── training/             # build_training_data, train_sentiment,
│   │                         # train_review_detector, evaluate_models
│   └── tests/                # pytest suite (69 tests)
├── sample_inputs/            # ready-made demo CSVs + paste text (3 real-named products)
├── docker-compose.yml
└── README.md
```

## Installation

### Backend setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Model training (once, before first run)

```bash
# Real-data pipeline (recommended):
python training/prepare_real_dataset.py    # downloads Amazon Reviews Multi (EN, 200k),
                                           # cleans, dedupes, stratified 80/10/10 split
                                           # (or use --input your_labelled.csv)
python training/train_sentiment_real.py    # TF-IDF (train only) -> MNB + LR,
                                           # selected on VALIDATION macro F1,
                                           # evaluated ONCE on the held-out test set,
                                           # gated promotion + automatic backup

# Review detector (synthetic demo data):
python training/train_review_detector.py   # TF-IDF char n-grams + NB/LR

python training/evaluate_models.py         # optional re-evaluation of saved artifacts
python training/check_sample_reviews.py    # sanity-check deployed model vs sample_reviews.csv
```

`train_sentiment_real.py` never overwrites the working model unless every promotion gate passes (validation macro F1 and held-out test macro F1 thresholds, test-vs-validation drop factor, and sample-review sanity checks). On success it backs up the previous artifacts to `backend/models_backup_<timestamp>/` and records validation metrics (per candidate), held-out test metrics, dataset provenance and class distribution in `metadata.json`; the earlier synthetic-data run is preserved there under `sentiment_synthetic_v1`.

The bundled synthetic datasets (`training/build_training_data.py` → `data/processed/*.csv`) remain as a runnable fallback demo; their results are **not** comparable to the real-data run.

### Frontend setup

```bash
cd frontend
npm install
# .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Project

```bash
# terminal 1 — backend (from backend/, venv active)
uvicorn main:app --reload

# terminal 2 — frontend (from frontend/)
npm run dev
```

Open http://localhost:3000 → **Analyze Reviews** → paste reviews or drop a CSV → watch the staged progress → explore the dashboard.

### Dataset format

CSV files need one column whose name (case-insensitive, substring match) is one of the review columns above. See `backend/data/sample_reviews.csv` for an example containing positive, negative, neutral, mixed, garbage, emoji, URL, non-review, suspicious, duplicate and near-duplicate rows.

## API Documentation

Interactive docs: **http://localhost:8000/docs** (Swagger) and **/redoc**.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Service + model-load status |
| POST | `/api/analyze/text` | Synchronous analysis of pasted reviews |
| POST | `/api/analyze/csv` | Async CSV job → `{analysis_id, status, progress, stage}` |
| GET | `/api/analysis/{id}` | Summary (sentiment, quality, aspects, pros/cons, verdict, statistics) |
| GET | `/api/analysis/{id}/status` | Job status + progress % for polling |
| GET | `/api/reviews/{id}` | Paginated reviews: `page`, `page_size`, `status`, `sentiment`, `suspicious`, `search`, `sort`, `order` |
| GET | `/api/aspects/{id}` | Aspect aggregation + pros/cons |
| GET | `/api/quality/{id}` | Quality report + verdict + statistics |
| GET | `/api/models` | Model metadata + evaluation metrics (all candidates) |
| GET | `/api/export/{id}` | `format=reviews_csv\|aspects_csv\|quality_json\|metrics_json\|analysis_json` |
| GET | `/api/products` | List stored products (name, review count, verdict, trust, quality) |
| GET | `/api/products/{pid}` | Product detail incl. latest analysis summary |
| POST | `/api/products/{pid}/reviews` | Append new reviews to a stored product and re-analyze |
| DELETE | `/api/products/{pid}` | Delete a stored product |
| GET | `/api/compare?ids=a,b` | Side-by-side comparison: verdicts, trust, quality, per-aspect ratings |
| GET | `/api/ask/{id}?q=...` | Ask-the-Reviews: question answering with evidence quotes |

### Example requests

```bash
# Paste analysis
curl -X POST http://localhost:8000/api/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Battery life is excellent.\nCamera is terrible but the display is bright."}'

# CSV upload (async)
curl -X POST http://localhost:8000/api/analyze/csv -F "file=@reviews.csv"

# Poll status
curl http://localhost:8000/api/analysis/{analysis_id}/status

# Paginated reviews, filtered
curl "http://localhost:8000/api/reviews/{analysis_id}?page=1&page_size=50&sentiment=Negative&suspicious=true"

# Export
curl -O -J "http://localhost:8000/api/export/{analysis_id}?format=reviews_csv"

# Store analysis as a product (My Products page)
curl -X POST http://localhost:8000/api/analyze/text -H "Content-Type: application/json" \n  -d '{"text": "...", "product_name": "Galaxy S24 Ultra"}'

# Add new reviews to that product later (auto re-analyzes)
curl -X POST http://localhost:8000/api/products/{product_id}/reviews -H "Content-Type: application/json" \n  -d '{"texts": ["New review one.", "New review two."]}'

# Compare two stored products
curl "http://localhost:8000/api/compare?ids={product_a},{product_b}"

# Ask the Reviews
curl "http://localhost:8000/api/ask/{analysis_id}?q=how%20is%20the%20camera%3F"
```

Structured errors (never raw stack traces):

```json
{
  "success": false,
  "error": { "code": "REVIEW_COLUMN_NOT_FOUND", "message": "Review column not found.",
             "details": { "detected_columns": ["id", "rating"] } }
}
```

## Testing

```bash
# backend (87 tests: validation, preprocessing, review detection, sentiment,
# aspects, quality, duplicates, products, ask, trust, end-to-end API)
cd backend && python -m pytest -q

# frontend (unit tests for API layer + utils)
cd frontend && npx vitest run
```

## Docker

```bash
docker compose up --build
# frontend: http://localhost:3000 · backend: http://localhost:8000
```

The backend image trains models at build time; the frontend image uses Next.js standalone output. The project also runs fully locally without Docker (see above).

## Security

- Only `.csv` uploads; size capped (`MAX_FILE_SIZE_MB`), row (`MAX_ROWS`), review-length (`MAX_REVIEW_LENGTH`) and total-volume (`MAX_TOTAL_TEXT_LENGTH`) limits.
- Uploads are treated as untrusted: binary signatures rejected, content parsed as data only, never executed.
- CSV exports are sanitized against spreadsheet formula injection (`=`, `+`, `-`, `@`, tab/CR prefixes neutralized).
- Structured error responses only — no Python exceptions, no server filesystem paths, no path traversal surface.
- CORS restricted to the configured frontend origin(s) (`CORS_ORIGINS` env; default `http://localhost:3000`). Set your production origin when deploying.
- Request/response validation via Pydantic; review content is not logged.

## Performance

- Models load **once** at startup (`ModelManager`), reused for every request.
- 3D scenes are `next/dynamic` lazy-loaded (`ssr: false`) and procedural (no asset downloads); the landing page renders its shell, hero and CTA before WebGL loads. The 3D scene is **not** loaded on inner pages.
- Large CSVs are parsed in chunks (`pandas.read_csv(chunksize=…)`), analysis runs in a background thread with staged progress.
- The API returns summary first; detailed reviews are fetched separately and paginated (`page_size` ≤ 200) — no multi-megabyte JSON blobs.
- Tables paginate; charts are virtualization-friendly; Zustand keeps client state minimal.

## Known Limitations

- The bundled training data is synthetic; real-world accuracy requires a representative labelled dataset.
- The aspect engine is lexicon/rule-based (transparent and explainable, but bounded by its dictionary).
- Suspicious-review signals are heuristics — they cannot prove a review is fake.
- Analysis results are held in memory (per process) — restarting the backend clears them; the store interface is designed for a later database swap.
- Confidence is calibrated model probability, not a guarantee of correctness.

## Future Improvements

- PostgreSQL-backed analysis store + auth/user workspaces.
- Transformer-based sentiment (distilled, optionally ONNX) with the same service layer.
- Learned aspect extraction (semi-supervised) to complement the dictionary.
- Streaming progress (SSE/WebSocket) instead of polling.
- Date-aware sentiment trend charts when review timestamps exist.
- Multilingual preprocessing and review columns.
cd C:\NLP\ecommerce-smart-review\backend
.venv\Scripts\activate
uvicorn main:app --reload
cd C:\NLP\ecommerce-smart-review\frontend
npm run dev