#!/usr/bin/env python3
"""
Translate PG essays from English to Chinese using Claude API.

Usage:
    python scripts/translate.py                    # Translate all pending essays
    python scripts/translate.py --slug do          # Translate a specific essay
    python scripts/translate.py --limit 5          # Translate up to 5 essays
    python scripts/translate.py --retranslate do   # Re-translate a specific essay
    python scripts/translate.py --status           # Show translation progress
"""

import argparse
import json
import sys
import time
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    ANTHROPIC_API_KEY,
    DATA_DIR,
    ESSAYS_DIR,
    TRANSLATION_BATCH_SIZE,
    TRANSLATION_MODEL,
    TRANSLATION_SYSTEM_PROMPT,
)


def load_essay(slug: str) -> dict | None:
    """Load an essay JSON file."""
    filepath = ESSAYS_DIR / f"{slug}.json"
    if not filepath.exists():
        return None
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_essay(data: dict):
    """Save essay data back to JSON."""
    filepath = ESSAYS_DIR / f"{data['slug']}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def translate_title(client: anthropic.Anthropic, title: str) -> str:
    """Translate an essay title."""
    response = client.messages.create(
        model=TRANSLATION_MODEL,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                f"请将以下 Paul Graham 文章标题翻译为简体中文，仅输出中文译文：\n\n{title}"
            ),
        }],
    )
    return response.content[0].text.strip()


def translate_paragraphs(
    client: anthropic.Anthropic,
    paragraphs: list[str],
    essay_title: str,
) -> list[str]:
    """Translate a list of English paragraphs to Chinese."""
    translated = []
    batch_size = TRANSLATION_BATCH_SIZE

    for i in range(0, len(paragraphs), batch_size):
        batch = paragraphs[i:i + batch_size]
        batch_text = "\n\n".join(
            f"[段落 {i + j + 1}]\n{para}" for j, para in enumerate(batch)
        )

        prompt = (
            f"以下是 Paul Graham 文章《{essay_title}》的段落，请逐段翻译为简体中文。\n"
            f"保持段落之间用空行分隔，每段前标注 [段落 N] 标记。\n\n"
            f"{batch_text}"
        )

        for attempt in range(3):
            try:
                response = client.messages.create(
                    model=TRANSLATION_MODEL,
                    max_tokens=4096,
                    system=TRANSLATION_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                result_text = response.content[0].text.strip()
                break
            except anthropic.APIError as e:
                print(f"    API error (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))
                else:
                    result_text = "\n\n".join(
                        f"[段落 {i + j + 1}]\n[翻译失败]" for j in range(len(batch))
                    )

        # Parse the response - extract translated paragraphs
        parts = result_text.split("[段落")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Remove the paragraph number marker
            lines = part.split("\n", 1)
            if len(lines) > 1:
                translated.append(lines[1].strip())
            elif lines[0]:
                # Try to extract after the "]" marker
                content = lines[0].split("]", 1)
                if len(content) > 1:
                    translated.append(content[1].strip())

        # If parsing failed, try simpler split
        if len(translated) < i + len(batch):
            # Fallback: treat the whole response as a single block and split by double newlines
            fallback_parts = result_text.split("\n\n")
            while len(translated) < i + len(batch) and fallback_parts:
                translated.append(fallback_parts.pop(0).strip())

        # Ensure we have enough paragraphs (pad with failure markers if needed)
        while len(translated) < i + len(batch):
            translated.append("[翻译失败]")

        time.sleep(0.5)  # Brief pause between batches

    return translated[:len(paragraphs)]


def translate_essay(client: anthropic.Anthropic, data: dict, retranslate: bool = False) -> bool:
    """Translate a single essay. Returns True if successful."""
    slug = data["slug"]
    title = data.get("title", slug)

    if not data.get("paragraphs_en"):
        print(f"  {slug}: No English content, skipping")
        return False

    if not retranslate and data.get("translation_status") == "complete":
        print(f"  {slug}: Already translated, skipping")
        return True

    print(f"  Translating: {title} ({len(data['paragraphs_en'])} paragraphs)...")

    # Translate title
    if not data.get("title_zh") or retranslate:
        try:
            data["title_zh"] = translate_title(client, title)
            print(f"    Title: {title} → {data['title_zh']}")
        except Exception as e:
            print(f"    Title translation failed: {e}")
            data["title_zh"] = title  # Fallback to English

    # Translate paragraphs
    # Support resuming: start from where we left off
    existing_zh = data.get("paragraphs_zh", [])
    if retranslate:
        existing_zh = []
        data["paragraphs_zh"] = []

    if len(existing_zh) >= len(data["paragraphs_en"]):
        print(f"    All paragraphs already translated")
        data["translation_status"] = "complete"
        save_essay(data)
        return True

    remaining_en = data["paragraphs_en"][len(existing_zh):]
    print(f"    Translating {len(remaining_en)} remaining paragraphs...")

    translated = translate_paragraphs(client, remaining_en, title)
    data["paragraphs_zh"] = existing_zh + translated

    # Check for failures
    failures = sum(1 for p in data["paragraphs_zh"] if "[翻译失败]" in p)
    if failures > 0:
        data["translation_status"] = "partial"
        print(f"    WARNING: {failures} paragraphs failed to translate")
    else:
        data["translation_status"] = "complete"
        print(f"    Done: {len(data['paragraphs_zh'])} paragraphs translated")

    save_essay(data)
    return failures == 0


def get_translatable_essays() -> list[dict]:
    """Get all essays that should be translated (included, with content)."""
    essays = []
    for filepath in sorted(ESSAYS_DIR.glob("*.json")):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        # Only translate included essays with content
        if data.get("included", True) and data.get("paragraphs_en"):
            essays.append(data)
    return essays


def print_status():
    """Print translation progress."""
    total = 0
    complete = 0
    partial = 0
    pending = 0
    excluded = 0

    for filepath in sorted(ESSAYS_DIR.glob("*.json")):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        total += 1
        if not data.get("included", True):
            excluded += 1
        elif data.get("translation_status") == "complete":
            complete += 1
        elif data.get("translation_status") == "partial":
            partial += 1
        else:
            pending += 1

    print(f"\n=== Translation Progress ===")
    print(f"Total essays: {total}")
    print(f"Excluded (technical): {excluded}")
    print(f"Translatable: {total - excluded}")
    print(f"  Complete: {complete}")
    print(f"  Partial: {partial}")
    print(f"  Pending: {pending}")

    if total - excluded > 0:
        pct = complete / (total - excluded) * 100
        print(f"\nProgress: {pct:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Translate PG essays to Chinese")
    parser.add_argument("--slug", type=str, default="",
                        help="Translate a specific essay")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of essays to translate")
    parser.add_argument("--retranslate", type=str, default="",
                        help="Re-translate a specific essay")
    parser.add_argument("--status", action="store_true",
                        help="Show translation progress")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("  export ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    if args.retranslate:
        data = load_essay(args.retranslate)
        if not data:
            print(f"Essay '{args.retranslate}' not found")
            sys.exit(1)
        translate_essay(client, data, retranslate=True)
        return

    if args.slug:
        data = load_essay(args.slug)
        if not data:
            print(f"Essay '{args.slug}' not found")
            sys.exit(1)
        translate_essay(client, data)
        return

    # Translate all pending essays
    essays = get_translatable_essays()
    pending = [e for e in essays if e.get("translation_status") != "complete"]

    if not pending:
        print("All essays are already translated!")
        return

    if args.limit > 0:
        pending = pending[:args.limit]

    print(f"Translating {len(pending)} essays...\n")
    success = 0
    for i, data in enumerate(pending):
        print(f"[{i + 1}/{len(pending)}]")
        if translate_essay(client, data):
            success += 1
        time.sleep(1)  # Rate limit between essays

    print(f"\nDone: {success}/{len(pending)} essays translated successfully")
    print_status()


if __name__ == "__main__":
    main()
