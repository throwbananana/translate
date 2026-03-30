# 书籍翻译工具

一个面向长文档的桌面翻译工具，支持 PDF、TXT、EPUB、DOCX、Markdown，
可接入 Gemini、OpenAI、Claude、DeepSeek 以及兼容 OpenAI API 的本地/自定义服务。

## 当前状态

当前仓库仍处于快速迭代阶段。建议优先通过模板文件或环境变量配置 API Key，
不要把本地运行态文件（如 `translator_config.json`、`translation_memory.db`）直接提交到仓库。

## 功能概览

- 多格式导入：PDF / TXT / EPUB / DOCX / Markdown
- 多模型翻译：Gemini / OpenAI / Claude / DeepSeek / LM Studio / 兼容 OpenAI API 的自定义服务
- 翻译记忆库与术语表
- PDF OCR 扫描件支持
- 批量任务与断点续传

## 安装

### 1) Python 依赖

```bash
py -m pip install -r requirements.txt
```

### 2) OCR 系统依赖

OCR 不仅依赖 Python 包，还依赖系统组件：

- `pdf2image` 需要 Poppler（确保 `pdftoppm` 可执行）
- `pytesseract` 需要安装 Tesseract OCR 引擎，并确保 `tesseract` 在 PATH 中

常见安装方式：

- Windows：安装 Poppler 与 Tesseract，并把可执行文件目录加入 PATH
- macOS：可使用 Homebrew 安装 `poppler` 与 `tesseract`
- Linux：使用系统包管理器安装 `poppler-utils` 与 `tesseract-ocr`

## 配置

推荐优先使用环境变量保存敏感信息：

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DEEPSEEK_API_KEY`
- `CUSTOM_API_KEY`
- `LM_STUDIO_API_KEY`

如果你希望使用本地配置文件，请先复制模板：

```bash
copy translator_config.example.json translator_config.json
```

然后按需填写 API Key、模型和基础地址。

## 默认模型说明

- Gemini 默认：`gemini-2.5-flash`
- OpenAI 默认：`gpt-3.5-turbo`
- Claude 默认：`claude-haiku-4-5-20251001`
- DeepSeek 默认：`deepseek-chat`
- LM Studio 默认：`qwen2.5-7b-instruct-1m`

## 运行

```bash
py book_translator_gui.pyw
```

## 仓库约定

- `translator_config.example.json`：可提交的模板文件
- `translator_config.json`：本地运行态配置，不应提交
- `translation_memory.db`：本地翻译记忆库，不应提交

## 后续建议

- 为 `anthropic`、OCR、EPUB 等功能补充更细的可选依赖说明
- 增加 CI 与 `pytest` 测试入口
- 持续维护默认模型，避免使用已弃用模型
