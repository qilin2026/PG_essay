#!/usr/bin/env python3
"""
Classify PG essays into categories and mark which ones to include.

Filters out purely technical essays (Lisp, spam filtering, programming languages)
and keeps essays about ideas, writing, startups, life, and culture.

Usage:
    python scripts/classify.py                # Classify all essays
    python scripts/classify.py --dry-run      # Preview without saving
    python scripts/classify.py --stats        # Show classification stats
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    DATA_DIR,
    DEFAULT_OVERRIDES,
    ESSAYS_DIR,
    INDEX_FILE,
    OVERRIDES_FILE,
)

CATEGORIES = {
    "thought": "思想/哲学",
    "writing": "写作",
    "startup": "创业/商业",
    "life": "人生/成长",
    "culture": "社会/文化",
    "technical": "编程/技术",
    "spam": "垃圾邮件过滤",
    "lisp": "Lisp/编程语言",
    "other": "其他",
}

EXCLUDE_CATEGORIES = {"technical", "spam", "lisp"}

def load_overrides() -> dict:
    """Load manual overrides, creating default file if needed."""
    if OVERRIDES_FILE.exists():
        with open(OVERRIDES_FILE, encoding="utf-8") as f:
            return json.load(f)
    # Save defaults
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OVERRIDES_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_OVERRIDES, f, ensure_ascii=False, indent=2)
    return DEFAULT_OVERRIDES


def load_index() -> list[dict]:
    """Load essay index."""
    if not INDEX_FILE.exists():
        print("ERROR: essays.json not found. Run scrape.py first.")
        sys.exit(1)
    with open(INDEX_FILE, encoding="utf-8") as f:
        return json.load(f)


def classify_all(essays: list[dict], dry_run: bool = False) -> dict:
    """Classify all essays, using LLM for unclassified ones."""
    overrides = load_overrides()
    classifications = {}

    # First, apply manual overrides
    for essay in essays:
        slug = essay["slug"]
        if slug in overrides:
            override = overrides[slug]
            category = "lisp" if not override["included"] else "thought"
            classifications[slug] = {
                "category": category,
                "included": override["included"],
                "reason": override["reason"],
                "source": "manual_override",
            }

    # Find essays that need LLM classification
    unclassified = [e for e in essays if e["slug"] not in classifications]

    for essay in unclassified:
        slug = essay["slug"]
        title = essay["title"].lower()
        # Keyword-based heuristic classification
        if any(w in title for w in ["lisp", "arc", "accumulator"]):
            cat = "lisp"
        elif any(w in title for w in ["spam", "filter", "bayesian"]):
            cat = "spam"
        elif any(w in title for w in ["language", "programming", "compiler", "parsing"]):
            cat = "technical"
        elif any(w in title for w in ["startup", "investor", "funding", "founder", "yc "]):
            cat = "startup"
        elif any(w in title for w in ["writ", "essay"]):
            cat = "writing"
        else:
            cat = "thought"

        classifications[slug] = {
            "category": cat,
            "included": cat not in EXCLUDE_CATEGORIES,
            "reason": "Heuristic classification based on title",
            "source": "heuristic",
        }

    if not dry_run:
        # Save classifications
        output_path = DATA_DIR / "classifications.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(classifications, f, ensure_ascii=False, indent=2)
        print(f"Saved classifications to {output_path}")

        # Update individual essay JSON files
        for essay in essays:
            slug = essay["slug"]
            essay_file = ESSAYS_DIR / f"{slug}.json"
            if essay_file.exists():
                with open(essay_file, encoding="utf-8") as f:
                    data = json.load(f)
                clf = classifications.get(slug, {})
                data["category"] = clf.get("category", "other")
                data["included"] = clf.get("included", True)
                with open(essay_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    return classifications


def print_stats(classifications: dict):
    """Print classification statistics."""
    from collections import Counter
    cats = Counter(c["category"] for c in classifications.values())
    included = sum(1 for c in classifications.values() if c["included"])
    excluded = sum(1 for c in classifications.values() if not c["included"])

    print(f"\n=== Classification Stats ===")
    print(f"Total essays: {len(classifications)}")
    print(f"Included: {included}")
    print(f"Excluded: {excluded}")
    print(f"\nBy category:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        label = CATEGORIES.get(cat, cat)
        marker = "✗" if cat in EXCLUDE_CATEGORIES else "✓"
        print(f"  {marker} {label}: {count}")

    print(f"\nExcluded essays:")
    for slug, clf in sorted(classifications.items()):
        if not clf["included"]:
            print(f"  - {slug}: {clf['reason']}")


def main():
    parser = argparse.ArgumentParser(description="Classify PG essays")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview classification without saving")
    parser.add_argument("--stats", action="store_true",
                        help="Show classification statistics")
    args = parser.parse_args()

    essays = load_index()
    print(f"Loaded {len(essays)} essays from index")

    if args.stats:
        clf_path = DATA_DIR / "classifications.json"
        if not clf_path.exists():
            print("No classifications found. Run classify.py first.")
            sys.exit(1)
        with open(clf_path, encoding="utf-8") as f:
            classifications = json.load(f)
        print_stats(classifications)
        return

    print("Classifying essays...")
    classifications = classify_all(essays, dry_run=args.dry_run)
    print_stats(classifications)


if __name__ == "__main__":
    main()
