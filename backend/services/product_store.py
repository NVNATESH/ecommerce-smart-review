"""ProductStore — persistent, named product review collections.

Each product is a JSON file under backend/data/products/:
    { id, name, created_at, updated_at, reviews: [texts],
      analysis_id, summary, results }
Survives server restarts. Analysis results are stored alongside the raw
reviews so a product can be reopened (dashboard, ask, exports) without
re-running the pipeline."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR

PRODUCT_DIR = DATA_DIR / "products"


class ProductStore:
    def __init__(self, directory: Path | None = None):
        self.dir = Path(directory) if directory else PRODUCT_DIR
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._products: dict[str, dict] = {}
        self._by_name: dict[str, str] = {}
        self._load_all()

    # ---------- persistence ----------
    def _path(self, pid: str) -> Path:
        return self.dir / f"{pid}.json"

    def _save(self, pid: str) -> None:
        data = self._products[pid]
        self._path(pid).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    def _load_all(self) -> None:
        for f in self.dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self._products[data["id"]] = data
                self._by_name[data["name"].lower()] = data["id"]
            except Exception:
                continue  # skip corrupt files rather than fail startup

    # ---------- operations ----------
    def find_or_create(self, name: str) -> str:
        name = name.strip()
        with self._lock:
            pid = self._by_name.get(name.lower())
            if pid is None:
                pid = uuid.uuid4().hex[:12]
                now = datetime.now(timezone.utc).isoformat()
                self._products[pid] = {
                    "id": pid,
                    "name": name,
                    "created_at": now,
                    "updated_at": now,
                    "reviews": [],
                    "analysis_id": None,
                    "summary": None,
                    "results": [],
                }
                self._by_name[name.lower()] = pid
                self._save(pid)
            return pid

    def get(self, pid: str) -> dict | None:
        return self._products.get(pid)

    def list(self) -> list[dict]:
        out = []
        for d in self._products.values():
            s = d.get("summary") or {}
            out.append({
                "id": d["id"],
                "name": d["name"],
                "created_at": d["created_at"],
                "updated_at": d["updated_at"],
                "review_count": len(d["reviews"]),
                "analysis_id": d.get("analysis_id"),
                "verdict": (s.get("verdict") or {}).get("overall_sentiment"),
                "trust": (s.get("trust") or {}).get("score"),
                "quality": (s.get("quality") or {}).get("quality_score"),
            })
        out.sort(key=lambda x: x["updated_at"], reverse=True)
        return out

    def append_reviews(self, pid: str, texts: list[str]) -> list[str]:
        with self._lock:
            d = self._products[pid]
            d["reviews"] = list(d["reviews"]) + list(texts)
            d["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(pid)
            return list(d["reviews"])

    def save_analysis(self, pid: str, analysis_id: str, summary: dict, results: list) -> None:
        with self._lock:
            d = self._products[pid]
            d["analysis_id"] = analysis_id
            d["summary"] = summary
            d["results"] = [r.model_dump() for r in results]
            d["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(pid)

    def delete(self, pid: str) -> bool:
        with self._lock:
            d = self._products.pop(pid, None)
            if d is None:
                return False
            self._by_name.pop(d["name"].lower(), None)
        self._path(pid).unlink(missing_ok=True)
        return True

    def all_products(self) -> list[dict]:
        return list(self._products.values())
