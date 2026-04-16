#!/usr/bin/env python3
"""
Scrape Paul Graham's essay index and content.

Usage:
    python scripts/scrape.py                  # Scrape index + all essays
    python scripts/scrape.py --index-only     # Only scrape the article index
    python scripts/scrape.py --limit 10       # Scrape index + first 10 essays
    python scripts/scrape.py --slug do        # Scrape a single essay by slug
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Allow running as script or module
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    DATA_DIR,
    ESSAYS_DIR,
    INDEX_FILE,
    PG_ARTICLES_URL,
    PG_BASE_URL,
    REQUEST_DELAY,
    REQUEST_HEADERS,
)


def fetch_page(url: str) -> str | None:
    """Fetch a page with retries and proper headers."""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
            resp.raise_for_status()
            # Handle encoding: PG's site sometimes uses latin-1
            if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1"):
                resp.encoding = "utf-8"
            return resp.text
        except requests.RequestException as e:
            print(f"  Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
    return None


def parse_essay_index(html: str) -> list[dict]:
    """Parse the articles.html page and extract essay links."""
    soup = BeautifulSoup(html, "html.parser")
    essays = []
    seen_slugs = set()

    # PG's articles page: essay links are in <font> tags containing <a> tags
    # inside table cells. We look for all <a> tags that link to .html pages.
    for link in soup.find_all("a"):
        href = link.get("href", "")
        title = link.get_text(strip=True)

        # Skip non-essay links
        if not href or not title:
            continue
        if href.startswith("http") and "paulgraham.com" not in href:
            continue
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        if href in ("index.html", "articles.html"):
            continue

        # Extract slug from href
        if href.startswith("http"):
            # Full URL
            slug = href.rstrip("/").split("/")[-1]
        else:
            slug = href

        # Remove .html extension to get the slug
        if slug.endswith(".html"):
            slug = slug[:-5]

        if not slug or slug in seen_slugs:
            continue

        seen_slugs.add(slug)
        essays.append({
            "slug": slug,
            "title": title,
            "url": f"{PG_BASE_URL}/{slug}.html",
        })

    print(f"Found {len(essays)} essays in index")
    return essays


def extract_date(soup: BeautifulSoup) -> str:
    """Try to extract the date from an essay page."""
    month_pattern = re.compile(
        r"(January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{4}"
    )
    # Look in font tags first (most common location)
    for font in soup.find_all("font"):
        text = font.get_text(strip=True)
        match = month_pattern.search(text)
        if match:
            return match.group(0)

    # Fallback: search entire page text
    text = soup.get_text()
    match = month_pattern.search(text)
    if match:
        return match.group(0)

    return ""


def extract_essay_content(html: str) -> dict:
    """Extract essay body text, splitting into paragraphs."""
    soup = BeautifulSoup(html, "html.parser")

    date = extract_date(soup)

    # Find all tables - the essay body is typically in the 2nd+ table
    tables = soup.find_all("table")

    if len(tables) < 2:
        # Some pages have only one table or non-standard structure
        # Fall back to extracting all text from the page
        body = soup.get_text(separator="\n")
    else:
        # The main content table is usually the second one
        # Try tables from index 1 onward, pick the one with the most text
        best_table = None
        best_len = 0
        for table in tables[1:]:
            text = table.get_text(strip=True)
            if len(text) > best_len:
                best_len = len(text)
                best_table = table
        if best_table is None:
            best_table = tables[-1]
        body = best_table

    # Convert body to paragraphs
    if isinstance(body, str):
        raw_text = body
    else:
        # Replace <br><br> and <p> with paragraph markers
        for br in body.find_all("br"):
            br.replace_with("\n")
        for p in body.find_all("p"):
            p.insert_before("\n\n")
            p.insert_after("\n\n")
        raw_text = body.get_text()

    # Split into paragraphs
    paragraphs = []
    for para in re.split(r"\n\s*\n", raw_text):
        cleaned = para.strip()
        # Skip very short fragments (nav text, dates alone, etc.)
        if cleaned and len(cleaned) > 10:
            paragraphs.append(cleaned)

    return {
        "date": date,
        "paragraphs_en": paragraphs,
    }


def scrape_essay(slug: str, url: str) -> dict | None:
    """Scrape a single essay and return its data."""
    html = fetch_page(url)
    if not html:
        print(f"  FAILED to fetch {slug}")
        return None

    content = extract_essay_content(html)
    return {
        "slug": slug,
        "date": content["date"],
        "paragraphs_en": content["paragraphs_en"],
        "paragraphs_zh": [],
        "title_zh": "",
        "translation_status": "pending",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def save_essay(essay_data: dict, title: str):
    """Save essay data to JSON file."""
    slug = essay_data["slug"]
    essay_data["title"] = title
    filepath = ESSAYS_DIR / f"{slug}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(essay_data, f, ensure_ascii=False, indent=2)


def load_index() -> list[dict]:
    """Load existing essay index if available."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_index(essays: list[dict]):
    """Save essay index."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(essays, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Scrape Paul Graham essays")
    parser.add_argument("--index-only", action="store_true",
                        help="Only scrape the article index")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of essays to scrape (0 = all)")
    parser.add_argument("--slug", type=str, default="",
                        help="Scrape a single essay by slug")
    args = parser.parse_args()

    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ESSAYS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Fetch and parse the index
    print("Fetching essay index...")
    html = fetch_page(PG_ARTICLES_URL)
    if not html:
        print("ERROR: Could not fetch articles page. Exiting.")
        sys.exit(1)

    essays = parse_essay_index(html)
    save_index(essays)
    print(f"Saved index with {len(essays)} essays to {INDEX_FILE}")

    if args.index_only:
        return

    # Step 2: Scrape individual essays
    if args.slug:
        targets = [e for e in essays if e["slug"] == args.slug]
        if not targets:
            print(f"ERROR: Slug '{args.slug}' not found in index")
            sys.exit(1)
    elif args.limit > 0:
        targets = essays[:args.limit]
    else:
        targets = essays

    print(f"\nScraping {len(targets)} essays...")
    success = 0
    for i, essay in enumerate(targets):
        slug = essay["slug"]
        filepath = ESSAYS_DIR / f"{slug}.json"

        # Skip if already scraped
        if filepath.exists():
            print(f"  [{i+1}/{len(targets)}] {slug} - already scraped, skipping")
            success += 1
            continue

        print(f"  [{i+1}/{len(targets)}] {slug} - scraping...")
        data = scrape_essay(slug, essay["url"])
        if data:
            save_essay(data, essay["title"])
            success += 1
            print(f"    OK - {len(data['paragraphs_en'])} paragraphs")
        else:
            print(f"    FAILED")

        # Rate limit
        if i < len(targets) - 1:
            time.sleep(REQUEST_DELAY)

    print(f"\nDone: {success}/{len(targets)} essays scraped successfully")


if __name__ == "__main__":
    main()
