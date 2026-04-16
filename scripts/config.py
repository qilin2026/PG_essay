"""
Configuration for PG Essay Chinese Mirror pipeline.
"""

import os
from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ESSAYS_DIR = DATA_DIR / "essays"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SITE_DIR = PROJECT_ROOT / "site"
OVERRIDES_FILE = DATA_DIR / "overrides.json"
INDEX_FILE = DATA_DIR / "essays.json"

# --- Scraping ---
PG_BASE_URL = "https://paulgraham.com"
PG_ARTICLES_URL = f"{PG_BASE_URL}/articles.html"
REQUEST_DELAY = 1.0  # seconds between requests
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# --- Translation ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TRANSLATION_MODEL = "claude-sonnet-4-20250514"
TRANSLATION_BATCH_SIZE = 3  # paragraphs per API call
TRANSLATION_SYSTEM_PROMPT = """你正在将 Paul Graham 的文章翻译为简体中文。

要求：
- 保留作者对话式、深刻洞察的文风
- 技术术语准确翻译（startup=初创公司，venture capital=风险投资）
- 专有名词首次出现时中英对照，如：Y Combinator（Y Combinator）
- 保留脚注标记 [1] [2] 等，不做改动
- 仅输出中文译文，不添加任何解释或评论
- 译文应流畅自然，避免翻译腔"""

# --- Classification ---
CLASSIFY_MODEL = "claude-haiku-4-5-20251001"

# Manually curated overrides for borderline essays
# True = include, False = exclude
DEFAULT_OVERRIDES = {
    "hp": {"included": True, "reason": "Hackers and Painters - 核心是思想而非技术"},
    "avg": {"included": False, "reason": "Beating the Averages - 核心论点围绕 Lisp"},
    "rootsoflisp": {"included": False, "reason": "The Roots of Lisp - 纯 Lisp 技术"},
    "arc0": {"included": False, "reason": "Arc - Lisp 方言发布"},
    "arcll1": {"included": False, "reason": "Arc Language - 技术细节"},
    "ilc03": {"included": False, "reason": "ILC 2003 - Lisp 会议演讲"},
    "icad": {"included": False, "reason": "Lisp 在设计中的应用 - 纯技术"},
    "diff": {"included": False, "reason": "What Made Lisp Different - 纯 Lisp"},
    "fix": {"included": False, "reason": "Lisp 相关技术"},
    "lwba": {"included": False, "reason": "Lisp 技术文章"},
    "onlisp": {"included": False, "reason": "On Lisp - Lisp 编程书"},
    "progbot": {"included": False, "reason": "Programming Bottom-Up - Lisp 编程"},
    "accgen": {"included": False, "reason": "Accumulator Generator - 编程语言对比"},
    "spam": {"included": False, "reason": "A Plan for Spam - 垃圾邮件过滤技术"},
    "better": {"included": False, "reason": "Better Bayesian Filtering - 贝叶斯过滤技术"},
    "spamhausblacklist": {"included": False, "reason": "垃圾邮件技术"},
    "wfks": {"included": False, "reason": "Will Filters Kill Spam - 垃圾邮件过滤"},
    "ffb": {"included": False, "reason": "Filters that Fight Back - 反垃圾邮件技术"},
    "stopspam": {"included": False, "reason": "Stopping Spam - 垃圾邮件技术"},
    "langdes": {"included": False, "reason": "Five Questions about Language Design - 编程语言设计"},
    "power": {"included": False, "reason": "Succinctness is Power - 编程语言"},
    "hundred": {"included": False, "reason": "The Hundred-Year Language - 编程语言"},
    "popular": {"included": False, "reason": "Being Popular - 编程语言设计"},
    "pypar": {"included": False, "reason": "Python Paradox - 编程语言"},
    "reesoo": {"included": False, "reason": "技术相关"},
    "thist": {"included": False, "reason": "技术相关"},
    "prcmc": {"included": False, "reason": "技术相关"},
    "carl": {"included": False, "reason": "Carl - 技术人物"},
    "property": {"included": True, "reason": "关于知识产权的思考，非技术"},
    "gh": {"included": True, "reason": "Great Hackers - 虽标题偏技术但核心是人才与创造力"},
    # Heuristic classifier corrections
    "desres": {"included": True, "reason": "Design and Research - 关于设计哲学"},
    "iflisp": {"included": False, "reason": "If Lisp is So Great - Lisp 相关"},
    "noop": {"included": False, "reason": "Why Arc Isn't Especially Object-Oriented - Arc/Lisp"},
    "weird": {"included": False, "reason": "Weird Languages - 编程语言"},
    "head": {"included": False, "reason": "Holding a Program in One's Head - 编程技术"},
    "road": {"included": False, "reason": "The Other Road Ahead - Web 应用技术细节"},
    "javacover": {"included": False, "reason": "Java's Cover - 编程语言评论"},
    "gba": {"included": True, "reason": "The Word Hacker - 关于黑客文化而非技术"},
    "taste": {"included": True, "reason": "Taste for Makers - 关于品味和设计思想"},
    "mac": {"included": True, "reason": "Return of the Mac - 关于技术选择哲学"},
    "6631327": {"included": False, "reason": "软件专利号 - 技术法律"},
    "softwarepatents": {"included": False, "reason": "Are Software Patents Evil - 软件专利技术话题"},
    "altair": {"included": False, "reason": "What Microsoft Is this the Altair Basic of - 技术类比"},
    "hw": {"included": False, "reason": "The Hardware Renaissance - 硬件技术"},
}

# --- Site Generation ---
SITE_TITLE = "保罗·格雷厄姆文集"
SITE_SUBTITLE = "Paul Graham Essays in Chinese"
SITE_DISCLAIMER = "本站为 paulgraham.com 的中文翻译镜像，仅供学习交流。原文版权归 Paul Graham 所有。"
FONT_STACK = "'Microsoft YaHei', 'PingFang SC', 'Noto Sans SC', 'Hiragino Sans GB', Verdana, sans-serif"
