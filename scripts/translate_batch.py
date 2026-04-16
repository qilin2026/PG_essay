#!/usr/bin/env python3
"""
Batch translate all pending PG essays using Claude API.

This script is designed to be run with ANTHROPIC_API_KEY set.
It translates all included essays that haven't been translated yet,
with full resume support and progress tracking.

Usage:
    ANTHROPIC_API_KEY=sk-... python scripts/translate_batch.py
    ANTHROPIC_API_KEY=sk-... python scripts/translate_batch.py --limit 20
    ANTHROPIC_API_KEY=sk-... python scripts/translate_batch.py --slug greatwork
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_DIR, ESSAYS_DIR, TRANSLATION_MODEL, TRANSLATION_SYSTEM_PROMPT

TITLE_PROMPT = "请将以下 Paul Graham 文章标题翻译为简体中文。仅输出中文标题，不要有引号或其他标点：\n\n"


def translate_one_essay(client, essay_path: Path) -> bool:
    """Translate a single essay. Returns True on success."""
    with open(essay_path, encoding="utf-8") as f:
        data = json.load(f)

    slug = data["slug"]
    title = data.get("title", slug)

    if not data.get("included", True):
        return True
    if not data.get("paragraphs_en"):
        return True
    if data.get("translation_status") == "complete" and data.get("paragraphs_zh"):
        return True

    paras_en = data["paragraphs_en"]
    # Filter out very short navigational/date-only paragraphs
    paras_en = [p for p in paras_en if len(p) > 15]
    data["paragraphs_en"] = paras_en

    print(f"  [{slug}] Translating: {title} ({len(paras_en)} paragraphs)...")

    # Translate title
    if not data.get("title_zh"):
        try:
            resp = client.messages.create(
                model=TRANSLATION_MODEL,
                max_tokens=200,
                messages=[{"role": "user", "content": TITLE_PROMPT + title}],
            )
            data["title_zh"] = resp.content[0].text.strip().strip('"').strip("《》")
            print(f"    Title: {title} -> {data['title_zh']}")
        except Exception as e:
            print(f"    Title translation failed: {e}")
            data["title_zh"] = title

    # Translate paragraphs in chunks of ~2000 words
    translated = []
    chunk = []
    chunk_words = 0

    def flush_chunk():
        nonlocal chunk, chunk_words
        if not chunk:
            return
        text = "\n\n---\n\n".join(chunk)
        prompt = (
            f"请翻译以下 Paul Graham 文章《{title}》的段落。"
            f"每个段落之间用 --- 分隔。"
            f"请保持相同的分隔格式输出中文翻译。\n\n{text}"
        )
        for attempt in range(3):
            try:
                resp = client.messages.create(
                    model=TRANSLATION_MODEL,
                    max_tokens=8192,
                    system=TRANSLATION_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = resp.content[0].text.strip()
                parts = [p.strip() for p in result.split("---") if p.strip()]
                # Align: if we got different count, try to make it work
                if len(parts) == len(chunk):
                    translated.extend(parts)
                elif len(parts) > len(chunk):
                    translated.extend(parts[:len(chunk)])
                else:
                    translated.extend(parts)
                    while len(translated) < len(translated) + (len(chunk) - len(parts)):
                        translated.append("[翻译失败]")
                break
            except Exception as e:
                print(f"    Chunk translation error (attempt {attempt+1}): {e}")
                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))
                else:
                    translated.extend(["[翻译失败]"] * len(chunk))
        chunk = []
        chunk_words = 0
        time.sleep(0.3)

    for para in paras_en:
        words = len(para.split())
        if chunk_words + words > 2000 and chunk:
            flush_chunk()
        chunk.append(para)
        chunk_words += words

    flush_chunk()

    # Pad if needed
    while len(translated) < len(paras_en):
        translated.append("[翻译失败]")
    data["paragraphs_zh"] = translated[:len(paras_en)]

    failures = sum(1 for p in data["paragraphs_zh"] if "[翻译失败]" in p)
    data["translation_status"] = "partial" if failures > 0 else "complete"

    with open(essay_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    status = f"DONE ({len(data['paragraphs_zh'])} paras)" if failures == 0 else f"PARTIAL ({failures} failures)"
    print(f"    {status}")
    return failures == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--slug", type=str, default="")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    if args.slug:
        path = ESSAYS_DIR / f"{args.slug}.json"
        if not path.exists():
            print(f"Essay not found: {args.slug}")
            sys.exit(1)
        translate_one_essay(client, path)
        return

    # Get all pending essays
    pending = []
    for fp in sorted(ESSAYS_DIR.glob("*.json")):
        with open(fp) as f:
            d = json.load(f)
        if (d.get("included", True)
                and d.get("paragraphs_en")
                and d.get("translation_status") != "complete"):
            pending.append(fp)

    if not pending:
        print("All essays already translated!")
        return

    if args.limit > 0:
        pending = pending[:args.limit]

    print(f"Translating {len(pending)} essays...\n")
    success = 0
    for i, fp in enumerate(pending):
        print(f"[{i+1}/{len(pending)}]")
        if translate_one_essay(client, fp):
            success += 1
        time.sleep(0.5)

    print(f"\nDone: {success}/{len(pending)} essays translated")

    # Summary
    total = complete = partial = pend = 0
    for fp in ESSAYS_DIR.glob("*.json"):
        with open(fp) as f:
            d = json.load(f)
        if d.get("included", True) and d.get("paragraphs_en"):
            total += 1
            s = d.get("translation_status", "pending")
            if s == "complete": complete += 1
            elif s == "partial": partial += 1
            else: pend += 1
    print(f"\nProgress: {complete}/{total} complete, {partial} partial, {pend} pending")


if __name__ == "__main__":
    main()
