# TransKnowledge 项目指南

## 项目概述

文章翻译 Agent，自动将英文文章翻译成中文并保存到 Obsidian。

## 核心架构

```
src/
├── scraper.py      # 网页抓取，HTML→Markdown 转换
├── translator.py   # DeepSeek API 翻译，格式保护
├── image_handler.py # 并发图片下载
├── obsidian_writer.py # Obsidian 文件写入
├── processor.py    # 主处理流程
└── cli.py          # 命令行入口
```

## 关键设计决策

1. **格式保护系统**: `translator.py` 使用占位符保护代码块、表格、链接、URL
2. **代码块处理**: `scraper.py` 将 4 空格缩进转换为围栏代码块，自动检测语言
3. **表格修复**: 去除行尾空格，确保 `|` 正确结尾
4. **专有名词保护**: 翻译 prompt 中明确列出不翻译的 AI/大模型领域术语

## 翻译术语保护

翻译时以下术语保持英文原文（定义在 `translator.py` 的 prompt 中）:

- **模型名称**: Claude, GPT, Gemini, LLaMA, Mistral, DeepSeek, Opus, Sonnet, Haiku
- **技术术语**: Transformer, Attention, Token, Embedding, Fine-tuning, RLHF, RAG, Chain-of-Thought, Few-shot, Zero-shot, In-context Learning, Prompt, Agent, MCP, Tool Use
- **产品/框架**: LangChain, LlamaIndex, Hugging Face, OpenAI, Anthropic, Claude Code, Claude Agent SDK
- **通用技术词汇**: API, SDK, JSON, Markdown, Git, GitHub

如需添加新术语，修改 `translator.py` 第 99-103 行的 prompt

## 常用命令

```bash
# 翻译并保存到 Obsidian
python -m src https://example.com/article --save

# 运行测试
python -m pytest tests/ -v

# 生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html
```

## 配置文件

- `config/config.yaml` - 主配置（API、Obsidian 路径等）
- `.env` - 环境变量（DEEPSEEK_API_KEY, OBSIDIAN_VAULT_PATH）

## Obsidian 集成

- Vault 路径: `/Users/kexiangyu/Documents/Obsidian Vault`
- 文章目录: `Articles/Translations`
- 附件目录: `Attachments`

## 版本历史

- v1.0.2 (待发布): 翻译 prompt 优化，保护 AI/大模型领域专有名词不被翻译
- v1.0.1: 修复代码块和表格格式转换问题
- v1.0.0: 首个稳定版本

## 注意事项

- 测试套件: 65 个测试，核心模块覆盖率 90%+
- 修改代码后务必运行测试确保不破坏现有功能

## 开发规则（禁止违反）

### 1. 图片处理规则

**问题根源**: 在处理动态渲染页面（如 HuggingFace Spaces）时，实际内容在 iframe 中，base_url 应该是 iframe 的 URL，而不是主页面 URL。

**必须遵守的规则**:

1. **永远不要在 Markdown 层面修复图片 URL**
   - ❌ 错误: 在 Markdown 中将相对路径转换为绝对 URL
   - ✅ 正确: 在 HTML 转 Markdown **之前**，将 HTML 中的 img src 转换为绝对 URL
   - 原因: Markdown 应该反映 HTML 的真实状态，修复应该在源头进行

2. **图片下载失败时，优先解决根本原因**
   - ❌ 错误: 尝试在下载失败后修改 URL 或跳过图片
   - ✅ 正确: 检查 base_url 是否正确（特别是 iframe 场景）
   - ✅ 正确: 检查 HTTP 请求头是否完整（User-Agent, Referer 等）
   - ✅ 正确: 检查图片 URL 过滤规则是否误判

3. **动态渲染判断规则**
   - ❌ 错误: 使用域名白名单配置决定是否动态渲染
   - ✅ 正确: 先尝试静态抓取，检查内容长度，自动回退到动态渲染
   - 原因: 域名白名单需要维护，且无法覆盖所有情况

4. **图片 URL 过滤规则要精确**
   - ❌ 错误: 使用 `'ad.'` 过滤广告，会误判 `bad.png`
   - ✅ 正确: 使用 `'/ad.'` 只匹配路径中的广告目录
   - 原因: 过于宽泛的模式会误杀正常图片

### 2. 完整流程验证规则

**问题根源**: 只验证了中间步骤（图片下载成功），没有验证最终输出（图片是否正确嵌入到文章中）。

**必须遵守的规则**:

1. **验证完整的端到端流程**
   - ❌ 错误: 只检查图片是否下载成功
   - ✅ 正确: 检查最终文章中图片引用是否为 Obsidian 格式 `![[Attachments/...]]`
   - 原因: 中间步骤成功不代表最终结果正确

2. **修复问题时要追踪数据流**
   - ✅ 正确流程:
     1. HTML 中的 img src（可能是相对路径）
     2. `_convert_relative_image_urls()` 转换为绝对 URL
     3. `html2text` 转换为 Markdown（保留绝对 URL）
     4. `extract_images()` 从 HTML 提取绝对 URL 列表
     5. `batch_download()` 下载图片
     6. `convert_to_obsidian_embeds()` 匹配绝对 URL 并替换为 Obsidian 格式

3. **URL 匹配要考虑所有变体**
   - `convert_to_obsidian_embeds()` 需要匹配:
     - 原始 URL（可能是 Next.js 包装的）
     - 真实 URL（提取后的）
     - 相对路径（如果 HTML 转换时保留了）
     - URL 编码/解码变体

### 3. 历史错误案例

**案例 1: iframe base_url 问题**
- 错误: 使用主页面 URL 作为 base_url，导致图片 URL 错误
- 修复: `_fetch_dynamic()` 返回 `(html, actual_base_url)`，使用 iframe URL
- 教训: 动态渲染时要检查是否有 iframe，使用 iframe 的 URL 作为 base_url

**案例 2: 图片 URL 过滤误判**
- 错误: `'ad.'` 模式匹配了 `bad.png`
- 修复: 改为 `'/ad.'` 只匹配路径中的广告目录
- 教训: 过滤规则要精确，避免误杀

**案例 3: Markdown 中图片未转换**
- 错误: HTML 转 Markdown 时保留了相对路径，`convert_to_obsidian_embeds()` 无法匹配
- 修复: 添加 `_convert_relative_image_urls()` 在 HTML 转 Markdown 之前转换
- 教训: 数据转换要在正确的阶段进行，Markdown 应该反映 HTML 的真实状态
