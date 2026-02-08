# TransKnowledge - 文章翻译Agent

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/RookieDBA/transknowledge)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-65%20passed-brightgreen.svg)](./TEST_SUMMARY.md)
[![Coverage](https://img.shields.io/badge/coverage-63%25-yellow.svg)](./TEST_SUMMARY.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

自动将英文文章翻译成中文并保存到Obsidian的智能工具。

## ✨ 功能特性

- 🌐 **智能网页抓取**: 使用readability自动提取文章正文,过滤广告和导航
- ⚡ **动态内容渲染**: 集成Playwright支持JavaScript动态加载的页面(如HuggingFace Spaces)
- 🤖 **AI翻译**: 基于DeepSeek API的高质量翻译,保持格式完整性
- 🖼️ **图片处理**: 自动下载图片并转换为Obsidian格式引用 `![[Attachments/img.png]]`
- 📝 **格式保留**: 完美保持Markdown格式,包括代码块、链接、表格等
- 📚 **Obsidian集成**: 直接保存到Obsidian vault,支持frontmatter元数据
- 🔌 **Claude Code集成**: 支持通过Obsidian Skills与Claude Code协作
- ✅ **完整测试**: 65个测试用例,核心模块覆盖率90%+

## 🏗️ 架构设计

```
用户请求 (URL)
    ↓
[Python CLI 层]
    ├─ scraper.py: 网页抓取 → 提取正文 → 转换Markdown
    ├─ translator.py: DeepSeek翻译 + 格式保护
    ├─ image_handler.py: 并发下载图片 → Obsidian引用
    └─ obsidian_writer.py: 构建frontmatter → 保存笔记
    ↓
JSON 输出 + Obsidian 文件
```

**核心设计模式:**
- **格式保护系统**: 使用占位符保护代码块、链接、图片引用
- **并发图片下载**: 线程池并发下载,失败不阻塞主流程
- **模块化配置**: 环境变量 > YAML配置,灵活可扩展

## 📦 安装

### 1. 克隆项目

```bash
git clone https://github.com/RookieDBA/transknowledge.git
cd transknowledge
```

### 2. 安装依赖

**使用 conda 环境（推荐）:**

```bash
# 如果已有 conda 环境
pip install -r requirements.txt

# 安装 Playwright 浏览器（用于动态内容渲染）
playwright install chromium
```

**使用 venv 虚拟环境:**

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```env
DEEPSEEK_API_KEY=sk-your-api-key-here
OBSIDIAN_VAULT_PATH=/Users/yourusername/Documents/Obsidian Vault
```

### 4. 配置Obsidian路径

编辑 `config/config.yaml`:

```yaml
obsidian:
  vault_path: "/Users/yourusername/Documents/Obsidian Vault"
  articles_folder: "Articles/Translations"
  attachments_folder: "Attachments"
```

## 🚀 使用方法

本项目提供两种保存到Obsidian的方式:

### 方式一: 命令行工具 (自动化,推荐)

使用Python CLI工具自动完成翻译、图片下载和保存:

```bash
# 翻译并自动保存到 Obsidian
python -m src https://example.com/article --save

# 仅翻译并输出 JSON（不保存）
python -m src https://example.com/article

# 使用自定义配置文件
python -m src https://example.com/article --config config/custom.yaml --save

# 指定自定义文件名
python -m src https://example.com/article --save --filename my-article.md

# 查看所有选项
python -m src --help
```

### 方式二: Claude Code + Obsidian Skills (灵活)

通过Claude Code配合Obsidian Skills手动创建和编辑笔记,适合需要更多自定义的场景。

#### 安装 Obsidian Skills

```bash
# 克隆 obsidian-skills 仓库
git clone https://github.com/kepano/obsidian-skills.git /tmp/obsidian-skills

# 复制 skills 到 Claude Code 配置目录
mkdir -p ~/.claude/skills
cp -r /tmp/obsidian-skills/skills/* ~/.claude/skills/
```

安装后包含以下技能:
- **obsidian-markdown**: 创建和编辑 Obsidian Flavored Markdown
- **obsidian-bases**: 处理 Obsidian Bases 文件
- **json-canvas**: 处理 JSON Canvas 文件

#### 使用方式

在Claude Code中,你可以直接请求创建Obsidian笔记:

```
帮我在 Obsidian vault 中创建一个笔记,标题是"xxx",内容是"xxx"
```

Claude Code会使用obsidian-markdown skill来创建符合Obsidian格式的笔记,包括:
- 正确的 frontmatter 属性
- Wikilinks `[[]]` 格式
- Callouts `> [!note]`
- 嵌入 `![[image.png]]`

### 两种方式对比

| 特性 | 命令行工具 | Claude Code + Skills |
|------|-----------|---------------------|
| 自动翻译 | ✅ | ❌ (需手动提供内容) |
| 自动下载图片 | ✅ | ❌ |
| 批量处理 | ✅ | ❌ |
| 灵活编辑 | ❌ | ✅ |
| 交互式操作 | ❌ | ✅ |
| 自定义格式 | 有限 | 完全自定义 |

**推荐工作流**: 使用命令行工具翻译文章并保存,如需手动调整或创建额外笔记,使用Claude Code + Obsidian Skills。

### 输出示例

**使用 `--save` 选项时的 JSON 输出:**

```json
{
  "title": "理解人工智能的基础",
  "original_title": "Understanding the Basics of AI",
  "content": "# 理解人工智能的基础\n\n人工智能(AI)是...",
  "source_url": "https://example.com/article",
  "author": "John Doe",
  "publish_date": "2026-01-20",
  "translated_date": "2026-02-01T10:30:00",
  "images": ["img_understanding_ai_001.png", "img_understanding_ai_002.jpg"],
  "tags": ["translation", "article"],
  "obsidian_save": {
    "success": true,
    "file_path": "/Users/xxx/Obsidian Vault/Articles/Translations/20260201_understanding-ai.md",
    "filename": "20260201_understanding-ai.md",
    "title": "理解人工智能的基础",
    "images_count": 2
  }
}
```

### Obsidian笔记示例

保存到Obsidian的笔记格式:

```markdown
---
title: 理解人工智能的基础
original_title: Understanding the Basics of AI
source_url: https://example.com/article
author: John Doe
publish_date: 2026-01-20
translated_date: 2026-02-01T10:30:00
tags:
  - translation
  - article
---

# 理解人工智能的基础

人工智能(AI)是计算机科学的一个分支...

![[Attachments/img_understanding_ai_001.png]]

## 什么是机器学习

机器学习是人工智能的一个子集...
```

## 📁 项目结构

```
transknowledge/
├── src/
│   ├── __main__.py          # CLI 入口
│   ├── cli.py               # 命令行接口
│   ├── processor.py         # 主处理模块 (96% 覆盖率)
│   ├── scraper.py           # 网页抓取 (95% 覆盖率)
│   ├── translator.py        # DeepSeek 翻译
│   ├── image_handler.py     # 图片下载 (55% 覆盖率)
│   ├── obsidian_writer.py   # Obsidian 文件写入 (94% 覆盖率)
│   └── utils.py             # 工具函数 (81% 覆盖率)
├── tests/                   # 测试套件 (65个测试)
│   ├── test_utils.py        # 工具函数测试
│   ├── test_scraper.py      # 抓取模块测试
│   ├── test_image_handler.py # 图片处理测试
│   ├── test_obsidian_writer.py # 写入模块测试
│   └── test_processor.py    # 集成测试
├── config/
│   ├── config.yaml          # 主配置文件
│   └── config.example.yaml  # 配置示例
├── logs/                    # 日志目录
├── requirements.txt         # 依赖列表
├── .env                     # 环境变量(需创建)
├── .env.example             # 环境变量示例
├── TEST_SUMMARY.md          # 测试报告
└── README.md                # 本文件
```

## ⚙️ 配置说明

### API配置

```yaml
api:
  deepseek:
    model: "deepseek-chat"      # DeepSeek模型
    max_tokens: 4096            # 最大token数
    temperature: 0.3            # 温度参数(0.1-0.5推荐)
    base_url: "https://api.deepseek.com"
```

### 翻译配置

```yaml
translation:
  source_language: "English"
  target_language: "Chinese"
  preserve_code_blocks: true  # 保护代码块不被翻译
  chunk_size: 3000            # 分段翻译的大小
```

### 图片配置

```yaml
images:
  download_enabled: true
  max_size_mb: 10             # 最大图片大小
  timeout: 30                 # 下载超时时间
  filename_prefix: "img"      # 文件名前缀
  allowed_formats:            # 允许的格式
    - jpg
    - jpeg
    - png
    - gif
    - webp
    - svg
```

### 动态渲染配置

```yaml
scraper:
  dynamic_render:
    enabled: true             # 启用动态渲染
    timeout: 30               # 页面加载超时时间(秒)
    min_content_length: 500   # 内容最小长度阈值
```

### Obsidian配置

```yaml
obsidian:
  vault_path: "/path/to/vault"
  articles_folder: "Articles/Translations"
  attachments_folder: "Attachments"
  filename_format: "{date}_{slug}"  # 文件名格式
  date_format: "%Y%m%d"             # 日期格式
```

## 🔄 工作流程

1. **抓取文章**: 先尝试静态抓取，如内容不足自动切换到Playwright动态渲染
2. **提取元数据**: 从HTML meta标签提取作者、日期、描述等信息
3. **图片URL处理**: 将相对路径转换为绝对URL，支持iframe内容提取
4. **翻译内容**: DeepSeek API 翻译，使用占位符保护代码块和链接
5. **下载图片**: 并发下载到 Obsidian 附件文件夹（默认5个并发）
6. **格式转换**: 将图片引用转换为 `![[Attachments/img_xxx.png]]` 格式
7. **构建笔记**: 生成frontmatter元数据和完整的Markdown内容
8. **保存文件**: 写入到Obsidian vault指定目录
9. **输出结果**: 返回包含所有信息的JSON结果

## 🧪 测试

项目包含完整的测试套件:

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定模块测试
python -m pytest tests/test_utils.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html

# 查看HTML覆盖率报告
open htmlcov/index.html
```

**测试统计 (v1.0.0):**
- ✅ 总测试数: 65个
- ✅ 通过率: 100%
- ✅ 总体覆盖率: 63%
- ✅ 核心模块覆盖率: 90%+

详见 [TEST_SUMMARY.md](TEST_SUMMARY.md)

## ❓ 常见问题

### Q: 如何获取DeepSeek API密钥?

访问 [DeepSeek Platform](https://platform.deepseek.com/) 注册并创建API密钥。

### Q: 图片下载失败怎么办?

- 检查网络连接和图片URL有效性
- 查看 `logs/app.log` 了解详细错误
- 个别图片失败不会中断整个流程
- 可以调整 `images.timeout` 和 `images.max_size_mb` 配置

### Q: 翻译质量如何提升?

- 调整 `temperature` 参数 (0.1-0.5之间,越低越稳定)
- 使用更强大的DeepSeek模型
- 调整 `chunk_size` 以优化长文章翻译
- 在配置中添加特定的翻译指示

### Q: 如何自定义保存位置?

修改 `config/config.yaml` 中的 `obsidian.articles_folder`:

```yaml
obsidian:
  articles_folder: "Tech/Translations"  # 自定义路径
```

### Q: 支持哪些网站?

理论上支持所有标准HTML网站。对于特殊网站:
- 使用readability提取正文,兼容性好
- 部分网站可能需要调整 `user_agent` 配置
- JavaScript动态加载的网站(如HuggingFace Spaces)会自动使用Playwright渲染
- 支持iframe嵌入内容的自动提取

## 🔧 故障排除

### 环境检查

```bash
# 检查Python版本(需要3.9+)
python --version

# 检查依赖安装
pip list | grep -E "openai|requests|beautifulsoup4"

# 测试API连接
python -c "from openai import OpenAI; print('API OK')"

# 测试配置加载
python -c "from src.utils import load_config; print(load_config())"
```

### 日志查看

```bash
# 实时查看日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log

# 查看最近50行
tail -n 50 logs/app.log
```

### 常见错误

**"No module named 'openai'"**
```bash
source venv/bin/activate  # 激活虚拟环境
pip install -r requirements.txt
```

**"Failed to fetch URL"**
- 检查网络连接
- 某些网站可能阻止自动化访问
- 查看日志了解详细错误: `tail -f logs/app.log`

**"Rate limit hit"**
- 翻译器有自动重试机制(60秒退避)
- 考虑调整 `chunk_size` 减少API调用
- 检查DeepSeek API配额

**"Images not downloading"**
- 确认 `images.download_enabled: true`
- 验证vault路径存在且有写权限
- 检查网络连接和图片URL有效性

## ⚠️ 注意事项

1. **API成本**: 翻译长文章会消耗较多API tokens,建议监控使用量
2. **网络要求**: 需要访问目标网站和DeepSeek API
3. **图片大小**: 默认限制10MB,可在配置中调整
4. **并发限制**: 图片下载默认5个并发,可根据网络情况调整
5. **文件覆盖**: 同名文件会被覆盖,建议检查输出路径
6. **格式保护**: 复杂的Markdown格式可能需要手动调整

## 🚧 路线图

**v1.1.0 (已完成):**
- [x] Playwright动态内容渲染支持
- [x] iframe内容自动提取
- [x] 图片相对路径自动转换
- [x] 增强的图片下载请求头
- [x] 智能静态/动态抓取切换

**v1.2.0 计划:**
- [ ] 批量处理URL列表
- [ ] RSS feed监控和自动翻译
- [ ] 支持更多翻译引擎(OpenAI, Claude)
- [ ] Web界面(Streamlit)
- [ ] 文章摘要生成
- [ ] 提高translator模块测试覆盖率

**v1.3.0 计划:**
- [ ] 支持更多语言对翻译
- [ ] 自定义翻译提示词
- [ ] 增量更新已翻译文章
- [ ] 翻译质量评估

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request!

**贡献指南:**
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

**开发环境设置:**
```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# 运行测试
pytest tests/ -v

# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/
```

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供高质量的AI翻译引擎
- [Obsidian](https://obsidian.md/) - 优秀的知识管理工具
- [Obsidian Skills](https://github.com/kepano/obsidian-skills) - Claude Code的Obsidian技能库
- [Readability](https://github.com/buriy/python-readability) - 智能文章提取
- [html2text](https://github.com/Alir3z4/html2text) - HTML到Markdown转换
- [Loguru](https://github.com/Delgan/loguru) - 优雅的日志库

## 📊 项目状态

- **版本**: v1.1.0
- **状态**: 稳定版本
- **Python**: 3.9+
- **测试**: 65个测试全部通过
- **覆盖率**: 63% (核心模块90%+)
- **最后更新**: 2026-02-08

---

**如有问题或建议,欢迎提交 [Issue](https://github.com/RookieDBA/transknowledge/issues)!**
