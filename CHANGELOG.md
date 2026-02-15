# Changelog

本文件记录 TransKnowledge 项目的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-02-08

### 新增

- **动态内容渲染支持**：集成 Playwright 支持 JavaScript 动态加载的页面（如 HuggingFace Spaces）
  - 自动检测静态抓取失败，智能回退到动态渲染
  - 支持 iframe 内容提取，正确处理嵌入式页面
  - 配置化的超时和内容长度阈值

- **图片处理增强**：
  - 在 HTML 转 Markdown 前将相对路径转换为绝对 URL
  - 支持 Next.js 等图片优化服务的 URL 提取
  - 增强 HTTP 请求头（User-Agent, Referer, Sec-Fetch-* 等）
  - 优化图片 URL 过滤规则，避免误判（如 `bad.png` 不再被 `ad.` 规则误杀）

- **开发规则文档**：在 CLAUDE.md 中新增"开发规则（禁止违反）"章节
  - 图片处理规则和最佳实践
  - 完整流程验证规则
  - 历史错误案例和教训总结

### 修复

- 修复动态渲染页面图片 URL 错误问题：使用 iframe URL 作为 base_url
- 修复图片未正确嵌入到文章的问题：确保 Markdown 中的图片引用被正确转换为 Obsidian 格式
- 修复图片过滤规则误判：将 `'ad.'` 改为 `'/ad.'` 只匹配路径中的广告目录
- 修复 HuggingFace Spaces 等动态页面的图片下载失败问题（19/19 图片全部成功）

### 变更

- `scraper.py`:
  - `fetch_url()` 现在返回 `(html, actual_base_url)` 元组
  - `_fetch_dynamic()` 返回 `(html, actual_base_url)` 元组
  - `_extract_iframe_content()` 返回 `(iframe_html, iframe_url)` 元组
  - 新增 `_convert_relative_image_urls()` 方法
  - 移除域名白名单配置，改用内容长度自动检测
  - 优化 `_is_valid_image_url()` 过滤规则

- `config/config.yaml`:
  - 移除 `scraper.dynamic_render.domains` 配置项
  - 保留 `enabled`、`timeout`、`min_content_length` 配置

- `requirements.txt`:
  - 新增 `playwright>=1.40.0` 依赖

### 性能

- 图片下载成功率从 1/18 提升到 19/19（100%）
- 所有图片正确嵌入为 Obsidian 格式 `![[Attachments/...]]`

## [1.0.1] - 2026-02-01

### 修复

- 修复代码块格式转换问题：将 4 空格缩进的代码块正确转换为围栏代码块（```）
- 修复表格格式问题：去除行尾多余空格，确保表格行以 `|` 正确结尾
- 修复翻译时 Markdown 元素被破坏的问题

### 新增

- 添加代码语言自动检测功能，支持 JSON、Python、JavaScript、Bash、HTML
- 增强翻译时的 Markdown 格式保护：
  - 保护完整表格块不被翻译破坏
  - 保护图片引用 `![]()` 和 `![[]]`
  - 保护普通链接 `[]()`
  - 保护独立 URL

### 变更

- `scraper.py`: 新增 `_preprocess_code_blocks()`、`_postprocess_markdown()`、`_detect_code_language()`、`_fix_table_format()` 方法
- `translator.py`: 增强 `_preserve_markdown_elements()` 方法的格式保护能力

## [1.0.0] - 2026-02-01

### 新增

- 首个稳定版本发布
- 智能网页抓取：使用 readability 自动提取文章正文
- AI 翻译：基于 DeepSeek API 的高质量翻译
- 图片处理：自动下载图片并转换为 Obsidian 格式引用
- 格式保留：保持 Markdown 格式完整性（代码块、链接、表格等）
- Obsidian 集成：直接保存到 Obsidian vault，支持 frontmatter 元数据
- Claude Code 集成：支持通过 Obsidian Skills 协作
- 完整测试套件：65 个测试用例，核心模块覆盖率 90%+
