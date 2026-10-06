"""Tests for the Ask-the-Reviews Q&A, Trust Score, evidence quotes and
emotion mix — the review-2 'extraordinary' feature set."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def analysis_id(client):
    text = "\n".join([
        "The battery life is excellent and easily lasts two days.",
        "Camera quality is terrible, photos come out blurry in daylight.",
        "Battery is amazing but the camera is disappointing.",
        "The phone heats up a lot while charging and the performance lags.",
        "Delivery was fast and the packaging was neat.",
        "Sound quality is superb and the build feels really premium.",
        "It has 128GB of storage and a 120Hz screen.",
        "The design is sleek and the colour looks elegant.",
    ])
    r = client.post("/api/analyze/text", json={"text": text})
    assert r.status_code == 200
    return r.json()["analysis_id"]


class TestAsk:
    def test_aspect_question_answered_with_quotes(self, client, analysis_id):
        r = client.get("/api/ask/" + analysis_id, params={"q": "how is the camera?"})
        assert r.status_code == 200
        body = r.json()
        assert body["matched"] >= 1
        assert "Camera" in body["answer"] or "camera" in body["answer"].lower()
        assert len(body["quotes"]) >= 1
        assert all("text" in q and "sentiment" in q for q in body["quotes"])

    def test_positive_aspect_tone(self, client, analysis_id):
        r = client.get("/api/ask/" + analysis_id, params={"q": "how is the battery?"})
        body = r.json()
        assert body["matched"] >= 1
        assert "happy" in body["answer"].lower() or body["breakdown"]["Positive"] >= body["breakdown"]["Negative"]

    def test_unmatched_question(self, client, analysis_id):
        r = client.get("/api/ask/" + analysis_id, params={"q": "quantum flux capacitor wormhole"})
        assert r.status_code == 200
        body = r.json()
        assert body["matched"] == 0
        assert "No reviews" in body["answer"]

    def test_overall_question(self, client, analysis_id):
        r = client.get("/api/ask/" + analysis_id, params={"q": "give me an overall verdict"})
        assert r.status_code == 200
        assert "reviews" in r.json()["answer"]

    def test_empty_question_rejected(self, client, analysis_id):
        r = client.get("/api/ask/" + analysis_id, params={"q": "  "})
        assert r.status_code in (400, 422)

    def test_unknown_analysis_404(self, client):
        r = client.get("/api/ask/doesnotexist", params={"q": "how is the battery?"})
        assert r.status_code == 404


class TestTrustAndEmotions:
    def test_trust_in_summary(self, client, analysis_id):
        r = client.get("/api/analysis/" + analysis_id)
        body = r.json()
        assert "trust" in body and body["trust"] is not None
        trust = body["trust"]
        assert 0 <= trust["score"] <= 100
        assert trust["band"] in {"High confidence", "Moderate confidence", "Low confidence"}
        assert "validReviewPct" in trust["components"]

    def test_emotions_in_summary(self, client, analysis_id):
        r = client.get("/api/analysis/" + analysis_id)
        body = r.json()
        assert "emotions" in body and body["emotions"]
        emotions = {e["emotion"]: e["count"] for e in body["emotions"]}
        assert set(emotions) >= {"Joy", "Anger", "Sadness", "Fear", "Love"}

    def test_pros_cons_have_evidence_quotes(self, client, analysis_id):
        r = client.get("/api/analysis/" + analysis_id)
        body = r.json()
        assert body["pros"], "expected at least one pro"
        for item in body["pros"] + body["cons"]:
            assert "quotes" in item


class TestEmojiNudge:
    def test_emoji_review_gets_positive_signal(self, client):
        r = client.post("/api/analyze/text", json={
            "text": "Got my new phone today 🙂🙂🙂🙂"
        })
        assert r.status_code == 200
        review = r.json()["reviews"][0]
        # emoji-only reviews (no sentiment words, no clauses) keep their
        # positive emoji signal instead of being pushed to Neutral/Negative
        assert review["sentiment"] in {"Positive", "Neutral"}
        assert review["positive_probability"] >= review["negative_probability"]

    def test_emoji_signal_recorded_in_preprocessing(self):
        from nlp.preprocessing import TextPreprocessor

        r = TextPreprocessor().preprocess("Great product 😍 bad service 😡")
        assert r.emoji_pos >= 1
        assert r.emoji_neg >= 1
