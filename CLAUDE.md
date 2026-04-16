# PG Essay 中文翻译镜像 — 项目快照

## 项目目标

构建 paulgraham.com 的中文翻译镜像网站。用户可以像浏览 PG 原站一样直接阅读中文翻译后的 essay。目标读者不是技术人员，关注的是 PG 的思想和写作，而非编程技术。

## 当前状态

- **基础设施已完成**：提取、分类、站点生成管线可用
- **221 篇文章已提取**（来自 ofou/graham-essays EPUB 存档）
- **26 篇纯技术文章已排除**（Lisp、垃圾邮件过滤、编程语言）
- **195 篇待翻译**（其中 188 篇有英文正文内容）
- **所有翻译已清除**，需要从头开始逐段忠实翻译
- **站点输出到 `docs/`**，用于 GitHub Pages 部署（需要仓库设为 Public）

## 翻译质量要求（极其重要）

1. **逐段忠实翻译** — 必须先读取 JSON 中的英文原文（paragraphs_en），逐段翻译，不可凭记忆概括
2. **保留所有细节** — PG 的具体例子、比喻、数据、人名、故事都必须完整保留
3. **注释和致谢必须翻译** — 原文中的 [1] [2] 等脚注和 "Thanks to..." 致谢部分都是正文的一部分，必须包含在翻译中
4. **保持 PG 的文风** — 对话式、深刻洞察、有时幽默，避免翻译腔
5. **每批只翻译 2-3 篇** — 质量优先于数量
6. **专有名词** — 首次出现时中英对照，如：Y Combinator（Y Combinator）

## 翻译工作流（核心）

采用"用户发原文 → Claude 翻译 → 用户验证 → 写入 JSON"的方式：

1. **用户发送原文** — 用户从 paulgraham.com 复制一篇文章的完整英文原文（包括注释和致谢），发送到对话中
2. **Claude 逐段翻译** — Claude 在对话中返回逐段中文翻译，用户可以直接对照原文检查质量
3. **用户确认满意后** — Claude 将翻译写入 `data/essays/{slug}.json`（更新 title_zh、paragraphs_zh、translation_status）
4. **定期生成站点** — 每完成几篇后运行 `python scripts/generate.py` 生成 HTML 到 `docs/`
5. **提交并推送** — `git add -A && git commit && git push`

## 项目结构

```
PG_essay/
├── CLAUDE.md              # 本文件 — 项目上下文快照
├── Makefile               # 构建命令
├── README.md              # 项目说明
├── requirements.txt       # Python 依赖：requests, beautifulsoup4, Jinja2, ebooklib
├── .gitignore
├── scripts/
│   ├── config.py          # 路径配置、分类覆盖列表、站点生成配置
│   ├── extract_epub.py    # 从 EPUB 提取文章内容到 data/essays/*.json
│   ├── classify.py        # 分类文章，筛除技术文章（启发式 + 手动覆盖）
│   └── generate.py        # 从翻译好的 JSON 生成静态 HTML 到 docs/
├── data/
│   ├── essays.json        # 文章索引（slug, title, date, url）
│   ├── classifications.json
│   ├── overrides.json     # 手动分类覆盖
│   └── essays/            # 每篇文章的 JSON，格式见下
├── templates/
│   ├── index.html         # 文章列表页 Jinja2 模板
│   └── essay.html         # 单篇文章页 Jinja2 模板
└── docs/                  # 生成的静态网站（GitHub Pages 部署目录）
```

## 单篇文章 JSON 格式

```json
{
  "slug": "vb",
  "title": "Life is Short",
  "title_zh": "",
  "date": "2016-01-01",
  "url": "https://paulgraham.com/vb.html",
  "category": "thought",
  "included": true,
  "paragraphs_en": ["Life is short, as everyone knows...", "..."],
  "paragraphs_zh": [],
  "translation_status": "pending",
  "scraped_at": "2026-04-16T..."
}
```

翻译完成后：
- `title_zh` 填入中文标题
- `paragraphs_zh` 填入逐段翻译（数量应与 paragraphs_en 一致）
- `translation_status` 改为 "complete"

## 写入翻译的方式

可以用 Python 脚本直接更新 JSON 文件：

```python
import json
filepath = "data/essays/{slug}.json"
with open(filepath) as f:
    data = json.load(f)
data["title_zh"] = "中文标题"
data["paragraphs_zh"] = ["第一段翻译...", "第二段翻译...", ...]
data["translation_status"] = "complete"
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## Git 信息

- 仓库：`qilin2026/PG_essay`
- 分支：`main`
- 仓库当前为 Private，需改为 Public 才能启用 GitHub Pages
- GitHub Pages 配置：Source = main 分支 /docs 目录

## 注意事项

- paulgraham.com 返回 403，无法直接抓取，英文内容来自 EPUB 存档
- 不需要 API Key — 翻译在对话中直接完成
- EPUB 提取的文本可能有轻微格式瑕疵（如连在一起的词），翻译时注意
