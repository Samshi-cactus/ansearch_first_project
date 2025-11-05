"""Basic integration tests for loading, filtering, and topic extraction."""

from __future__ import annotations

from src.loaders import detect_columns, filter_one_restaurant, load_any
from src.pipeline import extract_topics


def test_load_and_detect():
    """DataFrame loads and id/text columns are detected."""
    df = load_any("tests/data_fixture.jsonl")
    guess = detect_columns(df)
    assert guess.id_col and guess.text_col
    assert "gPlusPlaceId" in df.columns


def test_filter_and_extract_topics():
    """Filter one restaurant and extract topics without errors."""
    df = load_any("tests/data_fixture.jsonl")
    rid = "RID1"
    df1 = filter_one_restaurant(df, rid, id_col="gPlusPlaceId")
    assert len(df1) >= 2
    texts = df1["reviewText"].astype(str).tolist()
    topics, _ = extract_topics(texts, language="english", topk=5, min_docs=1)
    assert isinstance(topics, list)
