# 保罗·格雷厄姆文集 (Paul Graham Essays in Chinese)

paulgraham.com 中文翻译镜像站。

## 快速开始

```bash
# 1. 安装依赖
make install

# 2. 设置 API Key（翻译和分类需要）
export ANTHROPIC_API_KEY=your-key-here

# 3. 运行完整管线
make all

# 或者分步执行：
make scrape      # 抓取文章
make classify    # 分类筛选
make translate   # 翻译
make build       # 生成静态站点
```

## 项目结构

```
scripts/
  scrape.py      - 从 paulgraham.com 抓取文章索引和正文
  classify.py    - 用 LLM 分类文章，筛除纯技术文章
  translate.py   - 用 Claude API 翻译文章
  generate.py    - 用 Jinja2 模板生成静态 HTML
  config.py      - 配置文件

data/
  essays.json    - 文章索引
  essays/        - 每篇文章的 JSON 数据
  overrides.json - 手动分类覆盖

templates/
  index.html     - 文章列表页模板
  essay.html     - 单篇文章页模板

site/            - 生成的静态网站（部署目录）
```

## 管线流程

```
scrape → classify → translate → generate
  ↓         ↓          ↓           ↓
 抓取     筛选       翻译      生成 HTML
(~231篇)  (~180篇)   (Claude)   (site/)
```

## 声明

本站为 paulgraham.com 的中文翻译镜像，仅供学习交流。原文版权归 Paul Graham 所有。
