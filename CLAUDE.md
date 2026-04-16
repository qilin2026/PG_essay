# PG Essay 中文翻译镜像 — 项目快照

## 项目目标

构建 paulgraham.com 的中文翻译镜像网站。用户可以像浏览 PG 原站一样直接阅读中文翻译后的 essay。目标读者不是技术人员，关注的是 PG 的思想和写作，而非编程技术。

## 当前状态

- **基础设施已完成**：站点生成管线可用（generate.py + Jinja2 模板）
- **从零开始翻译** — 用户自行选择文章，从 paulgraham.com 复制原文发送
- **站点输出到 `docs/`** — 用于 GitHub Pages 部署（仓库已设为 Public）

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

### 长文处理（极其重要，必须遵守）

PG 的长文（80+ 段落，上万字）会导致 API 流式响应超时（stream idle timeout）。**无论是展示翻译还是写入 JSON，都必须分批处理。**

**展示翻译时**：每次只展示 ~20 段翻译，等用户确认后继续下一批。**绝对不要**试图在一条消息中输出全文翻译。

**写入 JSON 时**：见下方"写入翻译的方式"，每批 ~10-13 段。

**用户确认后直接写入**：如果用户说"确认没问题，直接写入"，不要再次输出翻译内容，立即开始分批写入 JSON。

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

**必须分批写入** — PG 的长文（80+ 段落）一次性写入会导致 API 流式响应超时（stream idle timeout）。解决方法：

1. 先用 `Write` 工具创建基础 JSON 文件（空的 paragraphs_en/zh）
2. 用多个 `Bash` 调用，每次通过 Python heredoc 脚本追加 ~10 段（英文 + 中文同步追加）
3. 最后一批设置 `translation_status = "complete"`

每批脚本模板：

```python
# 通过 Bash heredoc 执行: python3 << 'PYEOF' ... PYEOF
import json
data = json.load(open("data/essays/{slug}.json"))
data["paragraphs_en"].extend(["paragraph 1...", "paragraph 2...", ...])
data["paragraphs_zh"].extend(["第一段翻译...", "第二段翻译...", ...])
with open("data/essays/{slug}.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**关键约束**：每批不超过 ~10-13 段，避免单次 Bash 调用内容过长导致超时。

## Git 信息

- 仓库：`qilin2026/PG_essay`
- 分支：`main`
- 仓库当前为 Private，需改为 Public 才能启用 GitHub Pages
- GitHub Pages 配置：Source = main 分支 /docs 目录

## 注意事项

- paulgraham.com 返回 403，无法直接抓取，英文内容来自 EPUB 存档
- 不需要 API Key — 翻译在对话中直接完成
- EPUB 提取的文本可能有轻微格式瑕疵（如连在一起的词），翻译时注意
