"""End-to-end API tests via FastAPI TestClient (models must be trained)."""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


SAMPLE = """The battery life is excellent and the display is bright.
Camera quality is terrible and the microphone is weak.
The package arrived yesterday. The product has a 6.5 inch display.
Battery is amazing but the camera is disappointing.
BEST BEST BEST BEST BUY NOW!!!!
Battery life is excellent.
The battery backup is excellent.
Tomorrow I have my DBMS exam.
Battery life is excellent.
"""


class TestApi:
    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in {"ok", "degraded"}
        assert body["models_loaded"] is True

    def test_analyze_text_end_to_end(self, client):
        r = client.post("/api/analyze/text", json={"text": SAMPLE})
        assert r.status_code == 200
        body = r.json()
        assert body["analysis_id"]
        assert body["statistics"]["reviews_analyzed"] == 9
        assert 0 <= body["quality"]["quality_score"] <= 100
        assert body["quality"]["dataset_decision"] in {"ACCEPT", "ACCEPT WITH WARNING", "REJECT"}
        assert len(body["reviews"]) == 9
        # suspicious review detected
        suspicious = [rev for rev in body["reviews"] if rev["suspicious"]]
        assert suspicious and "BEST BEST" in suspicious[0]["original_text"]
        # duplicate + near duplicate flagged
        dup = [rev for rev in body["reviews"] if rev["duplicate"]]
        near = [rev for rev in body["reviews"] if rev["near_duplicate"]]
        assert dup and near
        # aspects extracted
        battery = next(a for a in body["aspects"] if a["aspect"] == "Battery")
        assert battery["mention_count"] >= 4

    def test_invalid_input_structured_error(self, client):
        r = client.post("/api/analyze/text", json={"text": "😀😀😀😀"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "EMOJI_ONLY"

    def test_empty_input(self, client):
        r = client.post("/api/analyze/text", json={"text": ""})
        assert r.json()["error"]["code"] == "EMPTY_INPUT"

    def test_analysis_not_found(self, client):
        r = client.get("/api/analysis/doesnotexist")
        assert r.status_code == 404

    def test_reviews_pagination(self, client):
        created = client.post("/api/analyze/text", json={"text": SAMPLE}).json()
        aid = created["analysis_id"]
        r = client.get(f"/api/reviews/{aid}?page=1&page_size=3")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 9
        assert len(body["reviews"]) == 3
        assert body["total_pages"] == 3

    def test_reviews_filter(self, client):
        created = client.post("/api/analyze/text", json={"text": SAMPLE}).json()
        r = client.get(f"/api/reviews/{created['analysis_id']}?sentiment=Positive")
        assert all(rev["sentiment"] == "Positive" for rev in r.json()["reviews"])

    def test_csv_upload_flow(self, client):
        csv_content = "review\n" + "".join(
            f'"{t}"\n' for t in [
                "The battery is excellent and lasts long.",
                "Camera is terrible and blurry.",
                "It has a 6.5 inch display and 128GB storage.",
                "Sound quality is superb.",
                "Performance lags a lot while gaming.",
            ]
        )
        r = client.post(
            "/api/analyze/csv",
            files={"file": ("reviews.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 200
        aid = r.json()["analysis_id"]
        # poll until completed
        import time

        for _ in range(100):
            status = client.get(f"/api/analysis/{aid}/status").json()
            if status["status"] in {"completed", "failed"}:
                break
            time.sleep(0.2)
        assert status["status"] == "completed", status
        summary = client.get(f"/api/analysis/{aid}")
        assert summary.status_code == 200
        assert summary.json()["statistics"]["reviews_analyzed"] == 5

    def test_export_reviews_csv(self, client):
        created = client.post("/api/analyze/text", json={"text": SAMPLE}).json()
        r = client.get(f"/api/export/{created['analysis_id']}?format=reviews_csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        assert b"review" in r.content

    def test_export_all_formats(self, client):
        created = client.post("/api/analyze/text", json={"text": SAMPLE}).json()
        for fmt in ("aspects_csv", "quality_json", "analysis_json", "metrics_json"):
            r = client.get(f"/api/export/{created['analysis_id']}?format={fmt}")
            assert r.status_code == 200, fmt

    def test_models_endpoint(self, client):
        r = client.get("/api/models")
        assert r.status_code == 200
        models = r.json()["models"]
        assert {m["task"] for m in models} == {"sentiment", "review_detector"}
        for m in models:
            assert m["selection_metric"].startswith("macro_f1")
            assert len(m["candidates"]) >= 2
