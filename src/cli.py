"""Command-line interface for running topic extraction on one restaurant."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

from src.loaders import detect_columns, filter_one_restaurant, load_any
from src.pipeline import extract_topics


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Extract topics from restaurant reviews."
    )
    parser.add_argument(
        "--input", required=True, help="Path to input CSV or JSONL file."
    )
    parser.add_argument(
        "--restaurant-id", required=True, help="Restaurant ID to filter by."
    )
    parser.add_argument(
        "--id-col", default="business_id", help="Column for restaurant ID."
    )
    parser.add_argument(
        "--text-col", default="reviewText", help="Column containing review text."
    )
    parser.add_argument(
        "--rating-col", default=None, help="Column for rating (optional)."
    )
    parser.add_argument(
        "--engine", default="simple", choices=["simple"], help="Topic engine."
    )
    parser.add_argument(
        "--lang", default="english", help="Language hint for stopwords."
    )
    parser.add_argument(
        "--topk", type=int, default=8, help="Top terms per topic label."
    )
    parser.add_argument(
        "--min-docs", type=int, default=2, help="Minimum docs per topic."
    )
    parser.add_argument("--out", required=True, help="Output JSON file path.")
    return parser.parse_args()


def main() -> None:
    """Load data, filter one restaurant, extract topics, and write JSON."""
    args = parse_args()
    df = load_any(args.input)

    cols = detect_columns(df, args.id_col, args.text_col, args.rating_col)
    id_col, text_col = cols.id_col, cols.text_col  # cols.rating_col optional / unused

    df_filtered = filter_one_restaurant(df, args.restaurant_id, id_col=id_col)
    texts = df_filtered[text_col].dropna().astype(str).tolist()

    topics, _ = extract_topics(
        texts, language=args.lang, topk=args.topk, min_docs=args.min_docs
    )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    output = {
        "metadata": {
            "engine": args.engine,
            "language": args.lang,
            "restaurant_id": args.restaurant_id,
            "n_docs": len(texts),
            "topk": args.topk,
            "min_docs": args.min_docs,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "topics": [t.__dict__ for t in topics],
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {args.out} with {len(topics)} topics")


if __name__ == "__main__":
    main()
