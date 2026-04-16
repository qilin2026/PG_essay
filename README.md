# 保罗·格雷厄姆文集 (Paul Graham Essays in Chinese)

paulgraham.com 中文翻译镜像站。

## 快速开始

```bash
# 安装依赖
make install

# 运行完整管线
make all
```

## 项目结构

```
scripts/
  extract_epub.py     - 从 EPUB 存档提取文章内容
  classify.py         - 分类文章，筛除纯技术文章
  apply_translations.py - 应用预生成的中文翻译
  generate.py         - 用 Jinja2 模板生成静态 HTML
  config.py           - 配置文件

data/
  essays.json         - 文章索引
  essays/             - 每篇文章的 JSON 数据
  overrides.json      - 手动分类覆盖
  classifications.json - 分类结果

templates/
  index.html          - 文章列表页模板
  essay.html          - 单篇文章页模板

site/                 - 生成的静态网站（部署目录）
```

## 管线流程

```
extract → classify → apply-translations → build
  ↓          ↓              ↓                ↓
从EPUB      筛选         应用翻译        生成 HTML
提取内容   (~195篇)      (中文)          (site/)
```

## 声明

本站为 paulgraham.com 的中文翻译镜像，仅供学习交流。原文版权归 Paul Graham 所有。
