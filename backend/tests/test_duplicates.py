"""Duplicate detection tests: exact + near duplicates are flagged, never deleted."""
from __future__ import annotations

from services.duplicate_service import DuplicateDetector


class TestDuplicates:
    def test_exact_duplicate_flagged(self):
        detector = DuplicateDetector()
        flags = detector.detect(["Battery life is excellent.", "Battery life is excellent."])
        assert flags[1]["duplicate"] is True
        assert flags[1]["duplicate_of"] == 0
        assert flags[0]["duplicate"] is False

    def test_near_duplicate_flagged(self):
        detector = DuplicateDetector()
        flags = detector.detect([
            "The battery life is excellent and lasts all day.",
            "The battery backup is excellent and lasts all day.",
            "The camera takes sharp photos at night.",
        ])
        assert flags[1]["near_duplicate"] is True or flags[1]["duplicate"] is True
        assert flags[2]["near_duplicate"] is False

    def test_nothing_deleted(self):
        detector = DuplicateDetector()
        flags = detector.detect(["Great phone.", "Great phone.", "Great phone."])
        assert len(flags) == 3  # all records kept, only flagged

    def test_summary_counts(self):
        detector = DuplicateDetector()
        flags = detector.detect(["Same text.", "Same text.", "Different text entirely here."])
        summary = DuplicateDetector.summarize(flags)
        assert summary["duplicates_removed"] == 1
        assert summary["near_duplicates_detected"] >= 0

    def test_kept_indices_exclude_exact_duplicates(self):
        detector = DuplicateDetector()
        flags = detector.detect(["A text.", "A text.", "B text."])
        kept = DuplicateDetector.kept_indices(flags)
        assert kept == [0, 2]
