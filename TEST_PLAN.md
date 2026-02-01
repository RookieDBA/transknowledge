# TransKnowladge 测试计划

## 测试目标
确保文章翻译工具的各个模块功能正常，包括网页抓取、翻译、图片处理、文件写入等核心功能。

## 测试范围

### 1. 工具函数模块 (utils.py)
- **测试内容**:
  - `slugify()`: 字符串转slug测试（中文、英文、特殊字符）
  - `validate_url()`: URL验证测试（有效/无效URL）
  - `load_config()`: 配置加载测试
  - `setup_logger()`: 日志设置测试

### 2. 网页抓取模块 (scraper.py)
- **测试内容**:
  - HTML解析和正文提取
  - 元数据提取（标题、作者、日期）
  - 图片URL提取
  - Markdown转换
- **测试方法**: 使用mock HTML内容，避免实际网络请求

### 3. 图片处理模块 (image_handler.py)
- **测试内容**:
  - 图片下载功能（使用mock）
  - 文件名生成
  - Obsidian格式转换
  - URL变体匹配（绝对路径/相对路径）
  - 错误处理（下载失败、文件过大）
- **测试方法**: Mock网络请求和文件操作

### 4. Obsidian写入模块 (obsidian_writer.py)
- **测试内容**:
  - Frontmatter构建
  - 文件名生成
  - 笔记内容构建
  - 文件保存
- **测试方法**: 使用临时目录进行文件操作测试

### 5. 翻译模块 (translator.py)
- **测试内容**:
  - 占位符保护机制（代码块、链接、图片）
  - 文本分块逻辑
  - API调用（使用mock）
  - 错误重试机制
- **测试方法**: Mock DeepSeek API响应

### 6. 主处理模块 (processor.py)
- **测试内容**:
  - 完整流程集成测试
  - 错误处理
  - 结果格式验证
- **测试方法**: Mock所有外部依赖

### 7. CLI模块 (cli.py)
- **测试内容**:
  - 参数解析
  - 命令执行
  - JSON输出格式
- **测试方法**: 使用subprocess或直接调用

## 测试工具
- **框架**: pytest
- **Mock**: unittest.mock
- **覆盖率**: pytest-cov

## 测试优先级
1. **高优先级**: utils, obsidian_writer, image_handler（核心功能）
2. **中优先级**: scraper, translator（依赖外部服务）
3. **低优先级**: processor, cli（集成测试）

## 成功标准
- 所有单元测试通过
- 代码覆盖率 > 70%
- 无严重Bug
- 边界情况处理正确
