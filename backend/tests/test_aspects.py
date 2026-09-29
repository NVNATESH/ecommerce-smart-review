"""Aspect engine tests: synonym normalization, clause polarity, contradictions."""
from __future__ import annotations

from nlp.aspect_engine import analyze, detect_aspects, review_level_sentiment


class TestAspectDetection:
    def test_battery_synonyms_normalize(self):
        for text in ("The battery is great.", "Battery life is great.", "Battery backup is great."):
            cats = detect_aspects(text)
            assert "Battery" in cats, text

    def test_display_synonyms(self):
        assert "Display" in detect_aspects("The screen is bright.")
        assert "Display" in detect_aspects("Display is sharp.")

    def test_two_aspects_two_sentiments(self):
        mentions, _ = analyze("The battery is excellent but the camera quality is terrible.")
        by_cat = {m.category: m.sentiment for m in mentions}
        assert by_cat.get("Battery") == "Positive"
        assert by_cat.get("Camera") == "Negative"

    def test_contradictory_review(self):
        mentions, clauses = analyze("The battery is amazing but the camera is terrible.")
        sentiments = {m.sentiment for m in mentions}
        assert "Positive" in sentiments and "Negative" in sentiments
        label, _ = review_level_sentiment(clauses)
        assert label == "Mixed"

    def test_no_aspect_no_mention(self):
        mentions, _ = analyze("Tomorrow I have my DBMS exam.")
        assert mentions == []

    def test_confidence_bounds(self):
        mentions, _ = analyze("The display is really stunning but the speaker sounds awful.")
        for m in mentions:
            assert 0.0 <= m.confidence <= 1.0

    def test_aspect_without_opinion_is_neutral(self):
        mentions, _ = analyze("It has a 6.5 inch display.")
        assert any(m.category == "Display" and m.sentiment == "Neutral" for m in mentions)

    def test_charging_category(self):
        assert "Charging" in detect_aspects("Fast charging works well.")
