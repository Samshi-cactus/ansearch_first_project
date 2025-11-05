"""Summarise per-restaurant topic JSONs into a CSV and brief printout."""

from __future__ import annotations

import csv
import glob
import json
import os
import re
from collections.abc import Iterable


def iter_topic_files(pattern: str) -> Iterable[str]:
    """Yield topic JSON paths matching the given glob pattern."""
    yield from sorted(glob.glob(pattern))


def main() -> None:
    """Build a CSV summary from topic files named topics_<ID>_<NAME>.json."""
    rows, skipped = [], []
    for path in iter_topic_files("output/*.json"):
        base = os.path.basename(path).removesuffix(".json")
        m = re.match(r"^topics_(\d+)_(.+)$", base)
        if not m:
            skipped.append(base)
            continue
        rid, rname = m.groups()
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        topics = d.get("topics", [])
        top1 = topics[0]["label"] if topics else ""
        rows.append(
            {
                "restaurant_id": rid,
                "name": rname,
                "n_topics": len(topics),
                "top_1": top1,
                "output_file": base + ".json",
            }
        )

    if rows:
        os.makedirs("output", exist_ok=True)
        out = "output/topic_summary.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ wrote {out}")
    else:
        print("No topic files found.")

    if skipped:
        print("⚠️ Skipped (fix names to topics_<ID>_<NAME>.json):")
        for s in skipped:
            print(" -", s)


if __name__ == "__main__":
    main()
