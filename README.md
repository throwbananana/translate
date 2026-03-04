# 书籍翻译工具 v2.3

一个功能完善的GUI工具，支持将PDF、TXT、EPUB格式的书籍翻译成指定语言（默认中文），可接入多种AI翻译API。内置翻译记忆库、术语表管理，并支持智能上下文翻译。

## 功能特点

- ✅ **多模型支持**：Google Gemini、OpenAI、Claude、DeepSeek、LM Studio (本地模型)
- ✅ **智能翻译引擎**：
    - 上下文记忆：根据前文保持连贯性
    - 翻译记忆库 (TM)：避免重复翻译相同句子
    - 术语表 (Glossary)：强制专有名词统一，**新增可视化编辑器**
    - 风格控制：小说、学术、武侠、新闻等多种风格
- ✅ **文件支持**：
    - **PDF (增强)**：集成 `pdfplumber` 优化排版，支持**扫描件 OCR 自动回退**
    - TXT、EPUB、DOCX、Markdown
- ✅ **章节导航**：**新增自动识别章节目录 (TOC) 侧边栏**，点击跳转
- ✅ **并发翻译**：支持多线程并发，大幅提升长篇小说翻译速度
- ✅ **双语导出**：一键生成双语对照 EPUB 电子书
- ✅ **在线搜索**：集成 Anna's Archive 和 Z-Library 搜索与下载
- ✅ **健壮性**：API配额用尽自动回退，支持断点续传，**批量任务持久化**

## 安装依赖

```bash
pip install -r requirements.txt
```

按需安装示例：

```bash
# 基础功能（TXT + OpenAI API）
pip install openai requests

# 添加PDF支持 (含OCR)
pip install PyPDF2 pdfplumber pdf2image pytesseract Pillow

# 添加EPUB支持
pip install ebooklib beautifulsoup4

# 添加Gemini API支持
pip install google-generativeai
```

## 快速测试（已预配置）

为了方便测试，已准备好：

1. 预配置的API Key：`translator_config.json` 默认包含一个示例Gemini API Key
2. 示例文本：`sample_book.txt`

```bash
# 1. 运行程序
python book_translator_gui.pyw

# 2. 点击“浏览...”选择 sample_book.txt
# 3. 点击“开始翻译”
# 4. 等待翻译完成后导出
```

---

## 使用方法

### 1. 运行程序

```bash
# Windows（无控制台窗口）
python book_translator_gui.pyw
```

### 2. 配置API

首次使用需要配置API：

1. 点击“配置API”按钮
2. 输入API Key和模型名称（以及 Base URL/LM Studio 端口）
3. 在主界面设置“目标语言”（默认中文，可自定义）
4. 点击“保存”

#### Gemini API配置示例
- API Key: 在 Google AI Studio 获取
- 模型: `gemini-2.5-flash`（推荐）或 `gemini-2.5-pro`

#### OpenAI API配置示例
- API Key: 在 OpenAI 获取
- 模型: `gpt-3.5-turbo` 或 `gpt-4`
- Base URL: (可选) 默认为OpenAI官方，可填写自定义地址

#### 自定义API配置示例
- 支持任何OpenAI兼容服务
- Base URL 示例: `https://api.example.com/v1`
- 模型: 服务支持的模型名称

#### 本地LM Studio（可直接选择或备用）
- 在“API类型”选择“本地 LM Studio”即可直连本地模型
- 默认无需额外配置，内置：`base_url=http://127.0.0.1:1234/v1`，`model=qwen2.5-7b-instruct-1m`
- 如果你在 LM Studio 中使用了其他端口/模型，可在“配置API”或 `translator_config.json` 中修改

#### 目标语言设置
- 主界面“目标语言”输入框可直接填写中文/English/日语等任意语言
- 默认为中文，修改后所有段落翻译与导出默认文件名都会使用该目标语言

### 3. 翻译书籍
1. 点击“浏览...”选择要翻译的文件
2. 等待文件加载完成
3. 点击“开始翻译”
4. 查看进度和实时译文

### 4. 导出译文
点击“导出译文”按钮，选择保存位置即可。
默认文件名会带上当前目标语言（例如：`sample_book_中文译文.txt`、`sample_book_English译文.txt`）。

### 5. 处理大文件（v1.1新功能）
- >10,000 字符自动进入预览模式（仅显示前 10,000 字符）
- 可点击“显示完整原文”查看全文
- 翻译始终使用完整文本，不受预览限制

### 6. 本地LM Studio备用翻译（v1.3新功能）
1. 在 LM Studio 中启动 OpenAI-Compatible Server（默认 http://127.0.0.1:1234/v1）
2. 选择并加载模型 ID：`qwen2.5-7b-instruct-1m`（或你在 LM Studio 中看到的模型标识）
3. 可在“API类型”中直接选择本地模式；程序在检测到 API 配额/限流错误时也会自动切换到本地 LM Studio，并在后续段落保持使用本地模型
4. LM Studio 需要的 `api_key` 仅作占位，可保持 `lm-studio`

> 提示：如需调整本地模型或端口，可修改 `translator_config.json` 的 `lm_studio` 配置后重启程序。

## 注意事项

### API费用
- 使用云端API会产生费用（Gemini有免费额度但有速率限制，OpenAI按token计费）
- 翻译长篇书籍前建议先用短文本验证成本

### 翻译质量
- 文本默认按约 800 字符分段翻译
- 不同API/模型风格不同，可在配置中更换模型

### 性能优化
- 翻译过程中程序会自动限速（0.5秒/段）避免API限流
- 可随时点击“停止翻译”中断翻译，已完成部分会保留

## 配置文件

程序会在同目录下创建 `translator_config.json` 保存API配置，包含：

```json
{
  "target_language": "中文",
  "api_configs": {
    "gemini": {
      "api_key": "your_gemini_api_key",
      "model": "gemini-2.5-flash"
    },
    "openai": {
      "api_key": "your_openai_api_key",
      "model": "gpt-3.5-turbo",
      "base_url": ""
    },
    "custom": {
      "api_key": "",
      "model": "",
      "base_url": ""
    },
    "lm_studio": {
      "api_key": "lm-studio",
      "model": "qwen2.5-7b-instruct-1m",
      "base_url": "http://127.0.0.1:1234/v1"
    }
  }
}
```

旧版配置（无 `api_configs` 包装或无 `target_language`）会自动兼容并在保存时升级。

请妥善保管此文件，避免泄露API Key。

## 故障排除

- `ModuleNotFoundError`: 使用 `pip install 包名` 安装缺失依赖
- API调用失败: 检查API Key、网络、配额/余额；如配额用完会自动切到本地模型
- PDF读取失败: 部分PDF为图片/特殊编码，可先转换为TXT或使用 pdfplumber

## 更新日志
### v2.3 (2025-12-24)
- ✅ **PDF 增强**：集成 `pdfplumber` 提升排版识别，新增 `OCR` (Tesseract) 自动回退功能，支持扫描件翻译。
- ✅ **术语表管理**：新增可视化术语表编辑器，支持增删改查和多表管理。
- ✅ **界面升级**：新增章节目录 (TOC) 侧边栏，支持点击跳转。
- ✅ **体验优化**：批量任务队列支持持久化保存，意外退出可恢复。

### v2.2 (2025-12-22)
- ✅ **架构重构**：统一使用 `TranslationEngine` 内核，提升稳定性和扩展性
- ✅ **新模型支持**：正式支持 **Claude 3** 和 **DeepSeek** API
- ✅ **智能增强**：
  - 新增翻译风格选择（小说/学术/直译等）
  - 上下文连贯性优化
  - 术语表与翻译记忆库深度集成
- ✅ **并发优化**：支持多线程并发翻译
- ✅ **日志系统**：新增详细日志记录 (`translator.log`)

### v1.4 (2025-12-10)
- ✅ 新增：主界面可自定义目标语言（中文/English/日语/法语等）
- ✅ 新增：本地 LM Studio 可作为独立 API 选项，支持自定义模型与端口并可测试连通性
- ✅ 配置文件增加 `target_language` 与 `api_configs` 包装，旧版自动兼容升级

### v1.3 (2025-12-09)
- ✅ 新增：云端配额用尽后自动切换到本地 LM Studio 模型（qwen2.5-7b-instruct-1m）
- ✅ 移除网页翻译与 Selenium 依赖，不再需要浏览器
- ✅ 配置文件新增 `lm_studio` 段，支持自定义本地端口/模型

### v1.2 (2025-12-05)
- ✅ 大文件智能预览模式优化
- ✅ 导出功能添加智能默认文件名与统计信息

### v1.1 (2025-12-01)
- ✅ 初始版本，支持PDF、TXT、EPUB，Gemini/OpenAI/自定义API，配置持久化
