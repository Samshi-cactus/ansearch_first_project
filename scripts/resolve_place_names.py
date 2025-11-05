"""
Suggest human-friendly restaurant names from a JSONL of reviews.

Heuristic (works even without spaCy):
1) Mine capitalised n-grams (1–3) that appear frequently in review text.
2) Prefer n-grams that contain food/venue hints (restaurant, deli, pizza, …).
3) Fall back to the most common capitalised token(s).
4) If spaCy is available, blend in top ORG entities with a small boost.

Outputs both a display name and a filesystem-friendly slug.

Usage:
    python scripts/resolve_place_names.py data/restaurant_*.jsonl
"""

from __future__ import annotations

import collections
import json
import re
import sys
import warnings
from pathlib import Path

# Optional spaCy (avoid hard dependency)
try:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Importing 'parser.split_arg_string' is deprecated",
            category=DeprecationWarning,
        )
        import spacy  # type: ignore

    _NLP = spacy.load("en_core_web_sm")
except (OSError, ImportError) as exc:
    _NLP = None
    print(f"[resolve_place_names] spaCy unavailable: {exc}")

FOOD_HINTS = {
    "restaurant",
    "deli",
    "pizza",
    "bar",
    "burger",
    "bakery",
    "cafe",
    "caf\u00e9",
    "sandwich",
    "bbq",
    "sushi",
    "grill",
    "taco",
    "steak",
    "ramen",
    "noodle",
    "joint",
    "pizzeria",
}

# Tokens to ignore as standalone "names"
COMMON_NOISE = {
    "the",
    "this",
    "that",
    "they",
    "you",
    "we",
    "my",
    "our",
    "nyc",
    "new",
    "york",
    "austin",
    "la",
    "el",
    "los",
    "gran",
    "via",
    # generic adjectives / frequent review words (single-token)
    "best",
    "great",
    "good",
    "amazing",
    "awesome",
    "nice",
    "love",
    "loved",
    "always",
    "never",
    "worst",
    "bad",
    "okay",
    "ok",
    "fine",
    # singletons we never want alone (still allow bigrams like "Home Slice")
    "home",
    "slice",
    "pizza",
}


def load_texts_from_jsonl(path: str | Path, text_col: str = "reviewText") -> list[str]:
    """Load review texts from a JSONL file."""
    texts: list[str] = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            txt = (obj.get(text_col) or "").strip()
            if txt:
                texts.append(str(txt))
    return texts


def capitalised_ngrams(text: str):
    """Yield capitalised tokens plus bi/tri-grams from a single text."""
    tokens = re.findall(r"\b[A-Z][A-Za-z'.&-]+\b", text)

    # 1-grams
    yield from tokens

    # 2-grams
    for i in range(len(tokens) - 1):
        yield f"{tokens[i]} {tokens[i + 1]}"

    # 3-grams
    for i in range(len(tokens) - 2):
        yield f"{tokens[i]} {tokens[i + 1]} {tokens[i + 2]}"


def rank_capitalised(texts: list[str]) -> list[tuple[str, int]]:
    """
    Return most common capitalised n-grams, highest first (tie-break by length).
    """
    counter: collections.Counter[str] = collections.Counter()
    for t in texts:
        for g in capitalised_ngrams(t):
            counter[g] += 1
    # Prefer longer n-grams when counts tie (e.g., "Home Slice" > "Home")
    return sorted(counter.items(), key=lambda kv: (kv[1], len(kv[0])), reverse=True)


def ner_orgs(texts: list[str], k: int = 20) -> list[tuple[str, int]]:
    """Return top-k ORG entities if spaCy is available; else empty list."""
    if not _NLP or not texts:
        return []
    blob = " ".join(texts[:1500])  # limit for speed and memory
    doc = _NLP(blob)
    orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
    counts = collections.Counter(orgs)
    return counts.most_common(k)


def _looks_like_business(phrase: str) -> bool:
    """Heuristic: a phrase that smells like a venue/business name."""
    phrase = phrase.strip()
    lower = phrase.lower()

    # Exclude obvious noise if it's a single token
    if " " not in phrase and lower in COMMON_NOISE:
        return False

    # Anything with an apostrophe (Katz's) or multiple words is promising
    if "'" in phrase or " " in phrase:
        return True

    # Single token with a food/venue hint is also ok (e.g., "Pizzeria")
    if any(h in lower for h in FOOD_HINTS):
        return True

    # Otherwise require some length to avoid "The", "Best", etc.
    return len(phrase) >= 4


def choose_name(candidates: list[tuple[str, int]]) -> str:
    """
    Pick the best display name from ranked candidates.

    Strategy:
    1) Prefer multi-word / possessive candidates that look like venues.
    2) Fall back to single-token candidates that aren't generic noise.
    """
    if not candidates:
        return "Unknown"

    # First pass: multi-word or possessive (e.g., "Home Slice", "Katz's")
    multi_like = [
        (name.strip(), cnt)
        for name, cnt in candidates
        if _looks_like_business(name) and (" " in name or "'" in name)
    ]
    if multi_like:
        # Already ranked upstream; keep that order
        return multi_like[0][0]

    # Second pass: non-noise single tokens
    singles = [
        (name.strip(), cnt)
        for name, cnt in candidates
        if _looks_like_business(name) and " " not in name and "'" not in name
    ]
    if singles:
        # Skip long ALLCAPS “ORGs” that are often false positives
        for name, _ in singles:
            if not (name.isupper() and len(name) > 6):
                return name

    # Fallback
    return candidates[0][0]


def slugify(name: str) -> str:
    """Simple filesystem-friendly slug."""
    s = name.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    s = re.sub(r"_+", "_", s)
    return s


def suggest_name_from_texts(texts: list[str]) -> tuple[str, str]:
    """Suggest (display_name, slug) from a list of review texts."""
    ranked = rank_capitalised(texts)

    # Blend in ORG entities if available (give them a small boost).
    org_rank = ner_orgs(texts, k=30)  # list[tuple[str, int]]
    if org_rank:
        org_boost = dict(org_rank)
        boosted: list[tuple[str, int]] = []
        for phrase, cnt in ranked:
            boosted.append((phrase, cnt + org_boost.get(phrase, 0)))
        # Tie-break by length so bigrams like "Home Slice" outrank "Home"
        boosted.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
        ranked = boosted

    best = choose_name(ranked)
    return best, slugify(best)


def suggest_name_from_file(path: str | Path) -> dict[str, str]:
    """Return {'name': display, 'slug': slug} suggestion for one JSONL file."""
    texts = load_texts_from_jsonl(path)
    name, slug = suggest_name_from_texts(texts)
    return {"name": name, "slug": slug}


def main(argv: list[str] | None = None) -> int:
    """CLI: print suggestions for each input file."""
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("Usage: resolve_place_names.py <file1.jsonl> [file2.jsonl ...]")
        return 2
    for p in argv:
        try:
            s = suggest_name_from_file(p)
        except OSError as exc:
            print(f"{p}: error reading file: {exc}")
            continue
        print(f"{Path(p).name:50s} → {s['name']}  ({s['slug']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
