"""FastAPI application entrypoint.

Startup: load trained models once into the ModelManager (never per request).
Routes stay thin; NLP/ML logic lives in services and engines.
"""
from __future__ import annotations

import logging
import logging.handlers
import sys
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_model_manager, get_pipeline, get_product_store, get_store
from api.errors import register_exception_handlers
from api.readiness import mark_ready
from api.routes import analysis, ask, export, health, models, products, reviews, upload
from config import API_PREFIX, APP_NAME, APP_VERSION, CORS_ORIGINS, LOG_LEVEL, LOGS_DIR

# --- logging ---------------------------------------------------------------
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=LOG_LEVEL.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            LOGS_DIR / "app.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("app")


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        lifespan=_lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS: only the frontend origin(s) are allowed (env-configurable).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=API_PREFIX, tags=["health"])
    app.include_router(analysis.router, prefix=API_PREFIX, tags=["analysis"])
    app.include_router(ask.router, prefix=API_PREFIX, tags=["ask"])
    app.include_router(products.router, prefix=API_PREFIX, tags=["products"])
    app.include_router(upload.router, prefix=API_PREFIX, tags=["analysis"])
    app.include_router(reviews.router, prefix=API_PREFIX, tags=["reviews"])
    app.include_router(models.router, prefix=API_PREFIX, tags=["models"])
    app.include_router(export.router, prefix=API_PREFIX, tags=["export"])

    register_exception_handlers(app)
    return app


async def _lifespan(app: FastAPI) -> None:
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)
    manager = get_model_manager()
    try:
        manager.load()
        get_pipeline()  # builds pipeline services once, validating wiring
        logger.info("Models loaded; starting NLP warm-up in background (port is live now).")
    except FileNotFoundError as exc:
        # Do not crash the whole API: /api/health reports "degraded" and
        # analysis endpoints return a structured 503 until models are trained.
        logger.error("%s", exc)
    threading.Thread(target=_startup_prepare, name="startup-warmup", daemon=True).start()
    yield
    logger.info("Shutting down.")


def _warm_up() -> None:
    """Trigger one-time lazy costs (NLTK WordNet load, TF-IDF feature names)."""
    pipeline = get_pipeline()
    sample = "Warmup: the battery lasts two days and charges in 30 minutes."
    pre = pipeline.preprocessing.preprocess(sample)
    pipeline.review_detector.score([sample])
    pipeline.sentiment.score([pre.model_text], [[]])
    get_model_manager().sentiment_vectorizer.get_feature_names_out()


def _startup_prepare() -> None:
    """One-time lazy costs (NLTK WordNet load, TF-IDF feature names, product
    hydration) run in a background thread — the port opens immediately and
    analysis routes wait on api.readiness for at most 30 s."""
    import time

    t0 = time.perf_counter()
    try:
        _warm_up()
        _hydrate_products()
    except Exception:
        logger.exception("Startup warm-up failed — first request will pay lazy costs instead.")
    finally:
        mark_ready()
    logger.info("Warm-up complete in %.1fs — application fully ready.", time.perf_counter() - t0)


def _hydrate_products() -> None:
    """Re-register stored product analyses into the in-memory store so saved
    products keep working (dashboard, ask, exports) across restarts."""
    from schemas.review import ReviewResult

    store = get_store()
    products = get_product_store()
    restored = 0
    for data in products.all_products():
        if data.get("summary") and data.get("results"):
            try:
                results = [ReviewResult.model_validate(r) for r in data["results"]]
                store.ingest(
                    data["id"],
                    {**data["summary"], "analysis_id": data["id"]},
                    results,
                )
                # also register under the latest run id so older saved
                # links keep working after a restart
                latest = data.get("analysis_id")
                if latest and latest != data["id"]:
                    store.ingest(
                        latest,
                        {**data["summary"], "analysis_id": latest},
                        results,
                    )
                restored += 1
            except Exception:
                logger.exception("Failed to restore product %s", data.get("name"))
    logger.info("Restored %d stored product analyses", restored)


app = create_app()
