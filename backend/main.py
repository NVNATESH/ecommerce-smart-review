"""FastAPI application entrypoint.

Startup: load trained models once into the ModelManager (never per request).
Routes stay thin; NLP/ML logic lives in services and engines.
"""
from __future__ import annotations

import logging
import logging.handlers
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_model_manager, get_pipeline
from api.errors import register_exception_handlers
from api.routes import analysis, export, health, models, reviews, upload
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
        _warm_up()
        logger.info("All models loaded; application ready.")
    except FileNotFoundError as exc:
        # Do not crash the whole API: /api/health reports "degraded" and
        # analysis endpoints return a structured 503 until models are trained.
        logger.error("%s", exc)
    yield
    logger.info("Shutting down.")


def _warm_up() -> None:
    """Trigger one-time lazy costs (NLTK WordNet load, TF-IDF feature names)
    during startup instead of on the first user request."""
    import time

    t0 = time.perf_counter()
    pipeline = get_pipeline()
    sample = "Warmup: the battery lasts two days and charges in 30 minutes."
    pre = pipeline.preprocessing.preprocess(sample)
    pipeline.review_detector.score([sample])
    pipeline.sentiment.score([pre.model_text], [[]])
    vectorizer = get_model_manager().sentiment_vectorizer
    vectorizer.get_feature_names_out()
    logger.info("Warm-up complete in %.1fs", time.perf_counter() - t0)


app = create_app()
