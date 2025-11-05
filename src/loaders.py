"""
Data loading and light utilities for the Topic Recurrence prototype.

This module intentionally stays minimal: resilient JSONL reading, simple column
detection, and per-restaurant filtering. It avoids heavy dependencies so that
fresh clones can run quickly.

Typical usage:
    df = load_any("data/restaurant_...jsonl")
    id_col, text_col, rating_col = detect_columns(df)
    df_one = filter_one_restaurant(df, restaurant_id="123", id_col=id_col)
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ColumnGuess:
    """Container for detected column names."""

    id_col: str
    text_col: str
    rating_col: str | None = None


def _read_jsonl(path: str) -> pd.DataFrame:
    """
    Read a JSONL file robustly (line-by-line, tolerant to minor errors).

    Args:
        path: Path to a .jsonl file.

    Returns:
        A pandas DataFrame. Missing keys become missing columns (pandas default).
    """
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip malformed lines instead of crashing.
                continue
    return pd.DataFrame.from_records(rows)


def load_any(path: str) -> pd.DataFrame:
    """
    Load CSV or JSONL into a DataFrame, choosing the right parser by extension.

    Args:
        path: Input file path (CSV or JSONL).

    Returns:
        DataFrame with columns as found in the file.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    lower = path.lower()
    if lower.endswith(".jsonl"):
        return _read_jsonl(path)
    if lower.endswith(".csv"):
        return pd.read_csv(path)
    raise ValueError("Unsupported file type. Use .csv or .jsonl")


def detect_columns(
    df: pd.DataFrame,
    id_col_hint: str | None = None,
    text_col_hint: str | None = None,
    rating_col_hint: str | None = None,
) -> ColumnGuess:
    """
    Detect the id/text/rating columns with simple heuristics + optional hints.

    Args:
        df: Loaded DataFrame.
        id_col_hint: If provided and present in df, use it.
        text_col_hint: If provided and present in df, use it.
        rating_col_hint: If provided and present in df, use it.

    Returns:
        ColumnGuess with resolved column names.

    Raises:
        ValueError if required columns cannot be found.
    """
    cols = {c.lower(): c for c in df.columns}

    # Helper to resolve a column by hint or candidates
    def resolve(
        hint: str | None, candidates: Iterable[str], required: bool
    ) -> str | None:
        if hint and hint in df.columns:
            return hint
        for cand in candidates:
            if cand.lower() in cols:
                return cols[cand.lower()]
        if required:
            raise ValueError(
                f"Could not detect required column. Tried: {list(candidates)}. "
                f"Found columns: {list(df.columns)}"
            )
        return None

    id_col = resolve(
        id_col_hint,
        candidates=("gPlusPlaceId", "business_id", "place_id", "restaurant_id", "id"),
        required=True,
    )
    text_col = resolve(
        text_col_hint,
        candidates=("reviewText", "text", "review_text", "content", "body"),
        required=True,
    )
    rating_col = resolve(
        rating_col_hint,
        candidates=("rating", "stars", "score"),
        required=False,
    )
    return ColumnGuess(id_col=id_col, text_col=text_col, rating_col=rating_col)


def filter_one_restaurant(
    df: pd.DataFrame,
    restaurant_id: str | int,
    *,
    id_col: str = "gPlusPlaceId",
    text_col: str = "reviewText",
) -> pd.DataFrame:
    """
    Return only rows for the given restaurant and non-empty review text.

    Parameters
    ----------
    df
        Input DataFrame containing at least the id and text columns.
    restaurant_id
        The place id to keep (matched as string).
    id_col
        Column name that holds the place id (default: "gPlusPlaceId").
    text_col
        Column name that holds the review text (default: "reviewText").

    Returns
    -------
    pd.DataFrame
        A copy of the filtered frame.

    Notes
    -----
    - Matches `restaurant_id` after casting ids to string, to be robust to
      mixed int/str sources.
    - Treats missing text as empty and strips whitespace.
    """
    if id_col not in df.columns or text_col not in df.columns:
        raise ValueError(
            f"Missing required columns: id_col='{id_col}', text_col='{text_col}'. "
            f"Available: {list(df.columns)}"
        )

    id_series = df[id_col].astype(str)
    text_series = df[text_col].fillna("").astype(str).str.strip()
    mask = (id_series == str(restaurant_id)) & (text_series != "")
    return df.loc[mask].copy()


def standardize(text: str) -> str:
    """
    Very light text standardization (lower + trim). Intentionally minimal.

    Args:
        text: Input string.

    Returns:
        Normalized string.
    """
    return (text or "").strip().lower()
