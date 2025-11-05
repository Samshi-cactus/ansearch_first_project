#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate 2>/dev/null || true
mkdir -p output

for f in data/restaurant_*_*.jsonl; do
  base="$(basename "$f")"
  rid="$(echo "$base" | sed -E 's/^restaurant_([0-9]+)_.+/\1/')"
  name="$(echo "$base" | sed -E 's/^restaurant_[0-9]+_(.+)\.jsonl/\1/')"
  python -m src.cli \
    --input "$f" \
    --restaurant-id "$rid" \
    --id-col gPlusPlaceId \
    --text-col reviewText \
    --engine simple \
    --min-docs 2 \
    --topk 8 \
    --out "output/topics_${rid}_${name}.json"
done
