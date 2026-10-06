"""Tests for stored products: save via product_name, append reviews,
persistence across restarts, compare, delete."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def phone_id(client):
    unique = uuid.uuid4().hex[:6]
    r = client.post("/api/analyze/text", json={
        "text": "\n".join([
            "The battery life is excellent and easily lasts two days.",
            "Camera quality is terrible, photos come out blurry.",
            "Battery is amazing but the camera is disappointing.",
            "Delivery was fast and the packaging was neat.",
        ]),
        "product_name": f"Phone X (test {unique})",
    })
    assert r.status_code == 200
    body = r.json()
    assert body.get("product_id"), body
    return body["product_id"]


class TestProducts:
    def test_product_saved_and_listed(self, client, phone_id):
        r = client.get("/api/products")
        assert r.status_code == 200
        products = r.json()["products"]
        match = [p for p in products if p["id"] == phone_id]
        assert match and match[0]["name"].startswith("Phone X (test")
        assert match[0]["review_count"] == 4
        assert match[0]["verdict"]

    def test_product_analysis_reachable(self, client, phone_id):
        r = client.get("/api/analysis/" + phone_id)
        assert r.status_code == 200
        assert r.json()["statistics"]["reviews_analyzed"] == 4

    def test_add_reviews_reanalyzes(self, client, phone_id):
        r = client.post(f"/api/products/{phone_id}/reviews", json={
            "texts": ["The screen is gorgeous and the speaker is loud.",
                      "Screen scratches very easily."]
        })
        assert r.status_code == 200
        body = r.json()
        assert body["review_count"] == 6
        # product analysis under the stable product id is updated
        summary = client.get("/api/analysis/" + phone_id).json()
        assert summary["statistics"]["reviews_analyzed"] == 6

    def test_product_reviews_paginated(self, client, phone_id):
        r = client.get(f"/api/products/{phone_id}/reviews", params={"page": 1, "page_size": 10})
        assert r.status_code == 200
        assert r.json()["total"] == 6

    def test_compare_two_products(self, client, phone_id):
        r2 = client.post("/api/analyze/text", json={
            "text": "\n".join([
                "Terrible battery, barely lasts an hour.",
                "The camera is stunning and the screen is beautiful.",
                "Excellent value for the price.",
            ]),
            "product_name": "Phone Y (test " + uuid.uuid4().hex[:6] + ")",
        })
        assert r2.status_code == 200
        y_id = r2.json()["product_id"]
        r = client.get("/api/compare", params={"ids": f"{phone_id},{y_id}"})
        assert r.status_code == 200
        data = r.json()
        assert len(data["products"]) == 2
        assert data["aspects"] and "Battery" in [a["aspect"] for a in data["aspects"]]

    def test_persistence_across_store_reload(self, client, phone_id, tmp_path):
        from services.product_store import ProductStore

        ps = ProductStore()  # fresh instance over the same directory
        assert ps.get(phone_id) is not None
        assert len(ps.get(phone_id)["reviews"]) == 6

    def test_delete_product(self, client):
        r = client.post("/api/analyze/text", json={
            "text": "Great battery.\nAwful camera.\nNice screen.",
            "product_name": "Temp Product (test " + uuid.uuid4().hex[:6] + ")",
        })
        pid = r.json()["product_id"]
        assert client.delete("/api/products/" + pid).status_code == 200
        assert client.get("/api/products/" + pid).status_code == 404
        assert client.delete("/api/products/" + pid).status_code == 404
