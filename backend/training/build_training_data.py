"""Builds the training datasets (deterministic, seeded).

Outputs:
    data/processed/train_sentiment.csv        (review, sentiment)
    data/processed/train_review_detector.csv  (text, label)

These are synthetic template-based datasets so the project is runnable
out of the box. They are NOT user data. Production-quality performance
requires a representative labelled dataset (documented in the README).

Usage:
    python training/build_training_data.py
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DATA_DIR  # noqa: E402

random.seed(42)

PROCESSED = DATA_DIR / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

PRODUCTS = ["phone", "laptop", "tablet", "smartwatch", "bluetooth speaker", "headphones", "camera"]

# aspect -> (positive adjectives, negative adjectives)
ASPECTS: dict[str, tuple[list[str], list[str]]] = {
    "battery": (["excellent", "amazing", "long-lasting", "reliable", "great", "superb", "outstanding"],
                ["terrible", "poor", "disappointing", "weak", "awful", "bad"]),
    "camera": (["excellent", "crisp", "sharp", "amazing", "fantastic", "impressive"],
               ["terrible", "blurry", "grainy", "poor", "awful", "useless"]),
    "display": (["bright", "vibrant", "sharp", "beautiful", "smooth", "great"],
                ["dull", "dim", "washed out", "grainy", "poor"]),
    "sound": (["superb", "clear", "loud", "rich", "amazing", "fantastic"],
              ["terrible", "tinny", "weak", "unclear", "awful"]),
    "microphone": (["clear", "great", "crisp", "reliable"],
                   ["weak", "unclear", "noisy", "terrible"]),
    "charging": (["fast", "quick", "reliable", "great"],
                 ["slow", "unreliable", "annoying", "poor"]),
    "performance": (["smooth", "fast", "snappy", "flawless", "excellent"],
                    ["laggy", "slow", "choppy", "terrible", "frustrating"]),
    "price": (["affordable", "reasonable", "great", "fair", "worth it"],
              ["expensive", "overpriced", "unreasonable", "too high"]),
    "delivery": (["fast", "quick", "on time", "great"],
                 ["slow", "delayed", "late", "terrible"]),
    "build quality": (["sturdy", "premium", "solid", "excellent"],
                      ["flimsy", "cheap", "fragile", "plasticky"]),
    "design": (["sleek", "beautiful", "modern", "elegant"],
               ["ugly", "outdated", "awkward"]),
    "heating": (["cool", "well managed", "controlled"],
                ["terrible", "annoying", "excessive", "bad"]),
    "keyboard": (["comfortable", "responsive", "great", "clicky"],
                 ["flimsy", "stiff", "uncomfortable"]),
    "software": (["smooth", "clean", "intuitive", "bug-free"],
                 ["buggy", "slow", "cluttered", "frustrating"]),
    "storage": (["spacious", "fast", "plenty", "generous"],
                ["limited", "slow", "small"]),
    "processor": (["powerful", "fast", "efficient", "great"],
                  ["weak", "slow", "outdated"]),
    "durability": (["durable", "long-lasting", "rugged", "reliable"],
                   ["fragile", "short-lived", "weak"]),
    "screen": (["bright", "sharp", "clear", "great"], ["dull", "dim", "scratched"]),
}

POS_TEMPLATES = [
    "The {aspect} is {adj}.",
    "I love the {aspect}, it is {adj}.",
    "The {aspect} on my {product} is {adj}.",
    "Honestly the {aspect} is {adj} for the price.",
    "Really happy with the {aspect}, it feels {adj}.",
    "The {aspect} works {adj} even after months of use.",
    "Best {aspect} I have used, absolutely {adj}.",
    "The {aspect} is {adj} and I would recommend this {product}.",
]

NEG_TEMPLATES = [
    "The {aspect} is {adj}.",
    "I regret buying this, the {aspect} is {adj}.",
    "The {aspect} on my {product} is {adj}.",
    "Very disappointed, the {aspect} is {adj}.",
    "The {aspect} is {adj} and support was not helpful either.",
    "Do not recommend it, the {aspect} is {adj}.",
    "The {aspect} became {adj} within a few weeks.",
]

MIXED_TEMPLATES = [
    "The {a1} is {p1} but the {a2} is {n1}.",
    "While the {a1} is {p1}, the {a2} is {n1}.",
    "The {a1} is {p1}, however the {a2} is {n1}.",
    "I like the {a1}, it is {p1}, but the {a2} is {n1}.",
]

NEUTRAL_TEMPLATES = [
    "The package arrived {day}. The {product} has a {num} display.",
    "It has a {num}mAh battery and {num}GB of storage.",
    "I bought this {product} {when}.",
    "The {product} supports fast charging and dual SIM.",
    "It came with a {num}W charger in the box.",
    "The screen is {num} inches with a {num}Hz refresh rate.",
    "My order number is {num}. The product was listed with a {num} inch screen.",
    "The {product} weighs {num} grams.",
]

DAYS = ["yesterday", "on Monday", "last week", "two days ago", "today"]
WHENS = ["last month", "in January", "two months ago", "last week"]
NUMS = [4, 5, 6.5, 6.7, 8, 12, 120, 144, 5000, 6000, 128, 256, 33, 65, 20000, 45000]


def aspect_sentence(aspect: str, adj: str, template: str) -> str:
    return template.format(
        aspect=aspect, product=random.choice(PRODUCTS), adj=adj,
    )


def make_sentiment_rows(n_per_class: int = 220) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    aspects = list(ASPECTS.keys())
    for _ in range(n_per_class):
        a1 = random.choice(aspects)
        pos_adjs, neg_adjs = ASPECTS[a1]

        # Positive
        t = random.choice(POS_TEMPLATES)
        rows.append((aspect_sentence(a1, random.choice(pos_adjs), t), "Positive"))

        # Negative
        t = random.choice(NEG_TEMPLATES)
        rows.append((aspect_sentence(a1, random.choice(neg_adjs), t), "Negative"))

        # Neutral
        rows.append((random.choice(NEUTRAL_TEMPLATES).format(
            product=random.choice(PRODUCTS), day=random.choice(DAYS),
            when=random.choice(WHENS),
            num=random.choice(NUMS),
        ), "Neutral"))

        # Mixed labelled Positive/Negative/Neutral depending on stronger cue is
        # avoided on purpose: mixed examples are kept in every majority class
        # pool via clause dominance below.
        a2 = random.choice([a for a in aspects if a != a1])
        _, neg2 = ASPECTS[a2]
        pos1, _ = ASPECTS[a1]
        mixed = random.choice(MIXED_TEMPLATES).format(
            a1=a1, p1=random.choice(pos1), a2=a2, n1=random.choice(neg2),
        )
        # For training the 3-class model, mixed sentences with a leading
        # positive clause are labelled Positive; leading negative are Negative.
        rows.append((mixed, "Positive" if random.random() < 0.5 else "Negative"))
    return rows


NOT_REVIEW_TEMPLATES = [
    "Tomorrow I have my DBMS exam.",
    "Where can I download the user manual?",
    "Please reset my account password.",
    "The meeting is scheduled at {num} PM.",
    "https://example.com",
    "www.shopping-site.com/deals/offer",
    "{num}",
    "asd123###",
    "####@@@@",
    "😀😀😀😀",
    "Send me the invoice for order {num}.",
    "How do I track my order?",
    "The capital of France is Paris.",
    "Water boils at {num} degrees.",
    "Chapter {num} discusses database normalization.",
    "Please call me back at {num}.",
    "Update: the server was down this morning.",
    "TODO: finish the assignment",
    "This is a system generated email. Do not reply.",
    "Terms and conditions apply.",
    "Welcome to our website!",
    "Click here to unsubscribe.",
    "The weather is nice today.",
    "I am learning machine learning this semester.",
    "{num} {num} {num}",
    "?????",
]


def make_detector_rows(n_not_review: int = 240) -> list[tuple[str, str]]:
    sentiment_rows = make_sentiment_rows(n_per_class=180)
    rows: list[tuple[str, str]] = [(text, "Review") for text, _ in sentiment_rows]
    for _ in range(n_not_review):
        rows.append((random.choice(NOT_REVIEW_TEMPLATES).format(
            num=random.choice(NUMS),
        ), "Not Review"))
    return rows


def write_csv(path: Path, header: list[str], rows: list[tuple[str, str]]) -> None:
    random.shuffle(rows)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} rows -> {path}")


if __name__ == "__main__":
    sentiment_rows = make_sentiment_rows(n_per_class=220)
    write_csv(PROCESSED / "train_sentiment.csv", ["review", "sentiment"], sentiment_rows)
    detector_rows = make_detector_rows(n_not_review=260)
    write_csv(PROCESSED / "train_review_detector.csv", ["text", "label"], detector_rows)
