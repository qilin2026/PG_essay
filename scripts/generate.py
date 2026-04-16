#!/usr/bin/env python3
"""
Generate static HTML site from translated essay data.

Usage:
    python scripts/generate.py              # Generate full site
    python scripts/generate.py --slug do    # Generate a single essay page
    python scripts/generate.py --dry-run    # Preview without writing files
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    ESSAYS_DIR,
    FONT_STACK,
    SITE_DIR,
    SITE_DISCLAIMER,
    SITE_SUBTITLE,
    SITE_TITLE,
    TEMPLATES_DIR,
)

# Month ordering for sorting essays by date
MONTH_ORDER = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def parse_date_sort_key(date_str: str) -> tuple[int, int]:
    """Parse 'Month Year' into a sortable tuple (year, month)."""
    if not date_str:
        return (0, 0)
    parts = date_str.strip().split()
    if len(parts) != 2:
        return (0, 0)
    month_name, year_str = parts
    try:
        year = int(year_str)
    except ValueError:
        return (0, 0)
    month = MONTH_ORDER.get(month_name, 0)
    return (year, month)


def load_essays() -> list[dict]:
    """Load all translated, included essays."""
    essays = []
    for filepath in ESSAYS_DIR.glob("*.json"):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        # Only include essays that are marked included and have translations
        if not data.get("included", True):
            continue
        if data.get("translation_status") not in ("complete", "partial"):
            continue
        if not data.get("paragraphs_zh"):
            continue

        essays.append(data)

    # Sort by date, newest first
    essays.sort(key=lambda e: parse_date_sort_key(e.get("date", "")), reverse=True)
    return essays


def generate_site(essays: list[dict], slug_filter: str = "", dry_run: bool = False):
    """Generate static HTML files."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,  # We control the HTML directly
    )

    template_vars = {
        "site_title": SITE_TITLE,
        "site_subtitle": SITE_SUBTITLE,
        "site_disclaimer": SITE_DISCLAIMER,
        "font_stack": FONT_STACK,
    }

    if not dry_run:
        SITE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate individual essay pages
    essay_template = env.get_template("essay.html")
    generated = 0

    for essay in essays:
        if slug_filter and essay["slug"] != slug_filter:
            continue

        html = essay_template.render(essay=essay, **template_vars)
        output_path = SITE_DIR / f"{essay['slug']}.html"

        if dry_run:
            print(f"  Would generate: {output_path} ({essay.get('title_zh', essay['title'])})")
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  Generated: {essay['slug']}.html - {essay.get('title_zh', essay['title'])}")
        generated += 1

    # Generate index page
    if not slug_filter:
        index_template = env.get_template("index.html")
        html = index_template.render(essays=essays, **template_vars)

        if dry_run:
            print(f"  Would generate: index.html ({len(essays)} essays)")
            print(f"  Would generate: articles.html (copy of index)")
        else:
            # Write index.html
            with open(SITE_DIR / "index.html", "w", encoding="utf-8") as f:
                f.write(html)
            # Also write articles.html as an alias (matching PG's URL)
            with open(SITE_DIR / "articles.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  Generated: index.html ({len(essays)} essays)")
            print(f"  Generated: articles.html (alias)")

    print(f"\nTotal: {generated} essay pages generated")
    if not dry_run and not slug_filter:
        print(f"Site output: {SITE_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="Generate PG essay Chinese mirror site")
    parser.add_argument("--slug", type=str, default="",
                        help="Generate page for a specific essay only")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing files")
    args = parser.parse_args()

    print("Loading translated essays...")
    essays = load_essays()

    if not essays:
        print("No translated essays found. Run translate.py first.")
        sys.exit(1)

    print(f"Found {len(essays)} translated essays\n")
    print("Generating site...")
    generate_site(essays, slug_filter=args.slug, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
