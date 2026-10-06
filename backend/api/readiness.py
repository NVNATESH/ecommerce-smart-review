"""Readiness gate — lets the port open immediately while the one-time NLP
warm-up (WordNet load, TF-IDF feature names, product hydration) finishes in
the background. Heavy routes wait on this event (max 30 s) instead of the
whole server being unreachable during startup."""
from __future__ import annotations

import threading

_READY = threading.Event()


def wait_until_ready(timeout: float = 30.0) -> bool:
    return _READY.wait(timeout)


def mark_ready() -> None:
    _READY.set()


def is_ready() -> bool:
    return _READY.is_set()
