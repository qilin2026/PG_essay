#!/usr/bin/env python3
"""
Extract essays from the graham-essays EPUB and CSV into our JSON format.

Usage:
    python scripts/extract_epub.py
"""

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_DIR, ESSAYS_DIR, INDEX_FILE

EPUB_PATH = "/tmp/graham.epub"
CSV_PATH = "/tmp/essays.csv"


def load_csv_index() -> list[dict]:
    """Load essay metadata from the CSV file."""
    essays = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row["URL"].strip()
            # Extract slug from URL
            if "paulgraham.com/" in url:
                slug = url.split("paulgraham.com/")[-1]
                if slug.endswith(".html"):
                    slug = slug[:-5]
            else:
                continue  # Skip non-standard URLs (like txt files)

            essays.append({
                "slug": slug,
                "title": row["Title"].strip(),
                "date": row.get("Date", "").strip(),
                "url": url,
            })
    return essays


def extract_epub_chapters() -> dict[str, list[str]]:
    """Extract chapters from EPUB, keyed by title."""
    book = epub.read_epub(EPUB_PATH)
    chapters = {}

    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        html_content = item.get_content().decode("utf-8", errors="replace")
        soup = BeautifulSoup(html_content, "html.parser")

        # Try to get the title from <h1> or <h2>
        title_tag = soup.find("h1") or soup.find("h2")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        if not title:
            continue

        # Remove the title element from the body
        title_tag.decompose()

        # Extract paragraphs
        paragraphs = []
        body = soup.find("body") or soup
        for element in body.find_all(["p", "blockquote"]):
            text = element.get_text(strip=True)
            if text and len(text) > 5:
                paragraphs.append(text)

        # If no <p> tags, try splitting by double newlines
        if not paragraphs:
            raw = body.get_text()
            for para in re.split(r"\n\s*\n", raw):
                cleaned = para.strip()
                if cleaned and len(cleaned) > 10:
                    paragraphs.append(cleaned)

        if paragraphs:
            chapters[title] = paragraphs

    return chapters


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy matching."""
    t = title.lower().strip()
    t = re.sub(r'["""\'\u2018\u2019\u201c\u201d]', '', t)
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[^a-z0-9 ]', '', t)
    return t.strip()


def match_chapters_to_index(
    csv_essays: list[dict],
    epub_chapters: dict[str, list[str]],
) -> list[dict]:
    """Match EPUB chapter content to CSV essay index."""
    # Build normalized title lookup
    norm_to_epub = {}
    for title, paras in epub_chapters.items():
        norm = normalize_title(title)
        norm_to_epub[norm] = (title, paras)

    matched = 0
    results = []

    for essay in csv_essays:
        slug = essay["slug"]
        norm = normalize_title(essay["title"])

        # Try exact normalized match
        if norm in norm_to_epub:
            epub_title, paras = norm_to_epub[norm]
            essay["paragraphs_en"] = paras
            matched += 1
        else:
            # Try partial matching
            best_match = None
            best_score = 0
            for enorm, (etitle, eparas) in norm_to_epub.items():
                # Simple overlap score
                words_a = set(norm.split())
                words_b = set(enorm.split())
                if not words_a or not words_b:
                    continue
                overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
                if overlap > best_score and overlap > 0.6:
                    best_score = overlap
                    best_match = (etitle, eparas)

            if best_match:
                epub_title, paras = best_match
                essay["paragraphs_en"] = paras
                matched += 1
            else:
                essay["paragraphs_en"] = []

        results.append(essay)

    print(f"Matched {matched}/{len(csv_essays)} essays to EPUB content")
    return results


def save_essays(essays: list[dict]):
    """Save all essay data to JSON files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ESSAYS_DIR.mkdir(parents=True, exist_ok=True)

    # Save index
    index = []
    for essay in essays:
        index.append({
            "slug": essay["slug"],
            "title": essay["title"],
            "date": essay.get("date", ""),
            "url": essay.get("url", ""),
        })

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # Save individual essays
    saved = 0
    for essay in essays:
        slug = essay["slug"]
        filepath = ESSAYS_DIR / f"{slug}.json"

        # Don't overwrite existing translations
        existing = {}
        if filepath.exists():
            with open(filepath, encoding="utf-8") as f:
                existing = json.load(f)

        data = {
            "slug": slug,
            "title": essay["title"],
            "title_zh": existing.get("title_zh", ""),
            "date": essay.get("date", ""),
            "url": essay.get("url", ""),
            "category": existing.get("category", ""),
            "included": existing.get("included", True),
            "paragraphs_en": essay.get("paragraphs_en", []),
            "paragraphs_zh": existing.get("paragraphs_zh", []),
            "translation_status": existing.get("translation_status", "pending"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        saved += 1

    print(f"Saved {saved} essay files to {ESSAYS_DIR}")
    print(f"Saved index with {len(index)} entries to {INDEX_FILE}")


def main():
    print("Loading CSV index...")
    csv_essays = load_csv_index()
    print(f"Found {len(csv_essays)} essays in CSV")

    print("\nExtracting EPUB chapters...")
    epub_chapters = extract_epub_chapters()
    print(f"Found {len(epub_chapters)} chapters in EPUB")

    print("\nMatching chapters to index...")
    essays = match_chapters_to_index(csv_essays, epub_chapters)

    # Stats
    with_content = sum(1 for e in essays if e.get("paragraphs_en"))
    print(f"\nEssays with content: {with_content}")
    print(f"Essays without content: {len(essays) - with_content}")

    print("\nSaving essays...")
    save_essays(essays)
    print("\nDone!")


if __name__ == "__main__":
    main()
