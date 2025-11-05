"""
Unit tests for the restaurant name resolution heuristics.

Covers:
- choose_name(): prefers realistic venue names, skips noise.
- suggest_name_from_file(): end-to-end on a tiny JSONL sample.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.resolve_place_names import (
    choose_name,
    suggest_name_from_file,
)

# Ensure project root (so "scripts" package is importable) is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_choose_name_prefers_business_like():
    """choose_name should select realistic venue-style names over generic noise."""
    candidates = [
        ("The", 30),  # noise
        ("Best", 12),  # noise
        ("Katz's", 10),  # realistic (apostrophe)
        ("Home Slice", 8),  # realistic (multi-word)
    ]
    chosen = choose_name(candidates)
    assert chosen in {"Katz's", "Home Slice"}


def test_choose_name_skips_all_caps_one_word_orgs():
    """Heuristic should avoid single long ALLCAPS tokens that are not good names."""
    candidates = [
        ("AWESOME", 50),  # should be skipped
        ("HOMESLICE", 25),  # should be skipped
        ("Home Slice", 10),  # acceptable fallback
    ]
    chosen = choose_name(candidates)
    assert chosen == "Home Slice"


def test_suggest_name_from_file_roundtrip(tmp_path: Path):
    """End-to-end: from a tiny JSONL file, produce a display name and slug."""
    p = tmp_path / "sample.jsonl"
    p.write_text(
        "\n".join(
            [
                '{"reviewText": "We loved eating at Home Slice Pizza!"}',
                '{"reviewText": "Home Slice has the best crust."}',
            ]
        ),
        encoding="utf-8",
    )

    result = suggest_name_from_file(p)
    assert isinstance(result, dict)
    assert "name" in result and "slug" in result
    # We do not hard-require a specific display name, but the slug should reflect it
    assert "home_slice" in result["slug"]
