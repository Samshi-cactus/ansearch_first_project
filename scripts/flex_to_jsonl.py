"""Convert flexible JSON input into JSONL lines of review objects.

Accepts:
- a single JSON object
- a list of JSON objects
- one-object-per-line mixed input

Usage:
    python scripts/flex_to_jsonl.py \
        data/reviews.clean.json \
        data/reviews_googleplus.jsonl
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path


def try_json(text: str) -> dict | None:
    """Best-effort parse of a JSON object; return None if it fails."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def as_iter(obj: object) -> list[dict] | None:
    """Return list of dicts for a parsed object, or None if incompatible."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
        return obj
    return None


def read_flex(path: Path) -> Iterator[dict]:
    """Yield dicts from a flexible JSON/JSONL file."""
    # First, try as a whole JSON file (object or list)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Cannot read {path}: {exc}") from exc

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    seq = as_iter(parsed)
    if seq is not None:
        yield from seq
        return

    # Fallback: one JSON object per line
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        obj = try_json(s)
        if obj is not None:
            yield obj


def main() -> None:
    """CLI entrypoint."""
    if len(sys.argv) != 3:
        raise SystemExit("Usage: flex_to_jsonl.py <input.json|jsonl> <output.jsonl>")

    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])

    n = 0
    with out.open("w", encoding="utf-8") as w:
        for obj in read_flex(inp):
            w.write(json.dumps(obj, ensure_ascii=False) + "\n")
            n += 1
    print(f"✅ Wrote {n} rows → {out}")


if __name__ == "__main__":
    main()
