#!/usr/bin/env python3
"""
Helper to apply inline translations to essay JSON files.
Called with a JSON string mapping slug -> {title_zh, paragraphs_zh}.
"""

import json
import sys
from pathlib import Path

ESSAYS_DIR = Path(__file__).resolve().parent.parent / "data" / "essays"


def apply(translations: dict):
    """Apply translations dict to essay files."""
    for slug, trans in translations.items():
        filepath = ESSAYS_DIR / f"{slug}.json"
        if not filepath.exists():
            print(f"SKIP: {slug} not found")
            continue
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        if trans.get("title_zh"):
            data["title_zh"] = trans["title_zh"]
        if trans.get("paragraphs_zh"):
            data["paragraphs_zh"] = trans["paragraphs_zh"]
            data["translation_status"] = "complete"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"OK: {slug} - {data.get('title_zh', slug)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            translations = json.load(f)
    else:
        translations = json.load(sys.stdin)
    apply(translations)
    print(f"\nApplied {len(translations)} translations")
