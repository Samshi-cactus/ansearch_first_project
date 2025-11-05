"""
Extract only restaurant entries and their categories
from a large Google Local Reviews JSONL file.

Reads a large file such as data/reviews_googleplus.jsonl, groups reviews by gPlusPlaceId,
and writes one lightweight summary file:

- data/restaurants_all.jsonl
  Each line: {"restaurant_id": "<id>", "name": "<suggested name>", "slug": "<slug>",
              "categories": [...], "n_reviews": N}

Only businesses whose categories include "restaurant" (case-insensitive)
are kept. No per-restaurant files are written.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

# --- ensure project root on sys.path ---
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# import smart name resolver
from scripts.resolve_place_names import suggest_name_from_texts  # noqa: E402

DATA_FILE = Path("data/reviews_googleplus.jsonl")  # large dataset (~5GB)
OUTPUT_FILE = Path("data/restaurants_all.jsonl")

# limit number of stored review texts per restaurant (for memory safety)
MAX_TEXTS_PER_RESTAURANT = 200


def slugify(text: str) -> str:
    """Create a filesystem-friendly slug."""
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return re.sub(r"_+", "_", s)


def iter_categories(raw) -> list[str]:
    """Yield clean category strings from None, string, list, set, or dict values."""
    if raw is None:
        return []
    if isinstance(raw, (list, set, tuple)):
        return [str(c).strip() for c in raw if str(c).strip()]
    if isinstance(raw, dict):
        # attempt to pull a name/title key if present
        for key in ("name", "label", "title"):
            if key in raw and str(raw[key]).strip():
                return [str(raw[key]).strip()]
        return [json.dumps(raw, ensure_ascii=False)]
    # fallback: treat scalar as comma-separated string
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def extract_all_restaurants() -> None:
    """Extract all restaurants (category contains 'restaurant') into one summary JSONL."""
    groups: dict[str, dict[str, object]] = defaultdict(
        lambda: {"texts": [], "categories": set(), "n_reviews": 0}
    )

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Source file not found: {DATA_FILE}. Place the dataset in data/."
        )

    print(f"🔎 Reading {DATA_FILE} ... this may take a while.")
    with open(DATA_FILE, encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f, 1):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            rid = obj.get("gPlusPlaceId")
            if not rid:
                continue

            g = groups[rid]
            g["n_reviews"] = int(g.get("n_reviews", 0)) + 1

            txt = obj.get("reviewText")
            if txt and len(g["texts"]) < MAX_TEXTS_PER_RESTAURANT:
                g["texts"].append(str(txt))

            for c in iter_categories(obj.get("categories")):
                g["categories"].add(c)

            if idx % 1_000_000 == 0:
                print(f"  ...processed {idx:,} lines")

    print(f"📦 Found {len(groups):,} unique business IDs. Filtering for restaurants...")

    kept = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as w:
        for rid, data in groups.items():
            cats = {c for c in data["categories"] if c}
            # ✅ Only keep entries that mention "restaurant" in any category
            if not any("restaurant" in c.lower() for c in cats):
                continue

            texts = [t for t in data["texts"] if t]  # type: ignore[index]
            name, slug = suggest_name_from_texts(texts)
            record = {
                "restaurant_id": rid,
                "name": name,
                "slug": slug,
                "categories": sorted(cats),
                "n_reviews": int(data["n_reviews"]),  # type: ignore[arg-type]
            }
            json.dump(record, w, ensure_ascii=False)
            w.write("\n")
            kept += 1

    print(f"✅ Done. Wrote {kept} restaurant entries → {OUTPUT_FILE}")
    print(f"Contains only businesses with 'restaurant' in their categories.")


if __name__ == "__main__":
    extract_all_restaurants()
