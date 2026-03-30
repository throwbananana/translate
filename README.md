# Book Translator

一个面向桌面端的多格式书籍翻译工具，支持 GUI 操作、多种翻译 API、本地模型回退、翻译记忆、术语表、批量任务和多种导出方式。

> 当前仓库主体代码已经不是“patch series 目录”，而是实际可运行的应用程序。本 README 以当前代码状态为准。

## 功能概览

- 支持输入格式：TXT、Markdown、PDF、EPUB、DOCX、RTF
- 支持翻译提供商：Gemini、OpenAI、Claude、DeepSeek、LM Studio、兼容 OpenAI 的自定义接口
- 支持自定义本地模型与云端额度耗尽后的回退
- 翻译记忆库（TM）与术语表注入
- 失败段落重试 / 人工修正
- 批量翻译任务与断点续传
- 网页导入、在线书源搜索、社区图书馆
- 导出纯文本、双语 EPUB、双语 DOCX、有声书、解析结果

## 快速开始

### 1. 安装 Python

推荐 Python 3.10 及以上。

### 2. 安装依赖

```bash
py -m pip install -r requirements.txt
```

如果你要运行测试：

```bash
py -m pip install -r requirements-dev.txt
```

### 3. 启动程序

Windows 下可直接双击：

```bash
start.bat
```

或者命令行启动：

```bash
py book_translator_gui.pyw
```

## 依赖说明

### 必选 Python 依赖

- `google-generativeai`
- `openai`
- `anthropic`
- `requests`
- `PyPDF2`
- `pdfplumber`
- `pdf2image`
- `ebooklib`
- `beautifulsoup4`
- `python-docx`
- `pytesseract`
- `Pillow`

### OCR / PDF 额外系统依赖

以下能力不是仅装 Python 包就能完全工作：

- `pdf2image` 依赖 **Poppler**
- `pytesseract` 依赖 **Tesseract OCR**

如果缺少系统组件，项目仍可运行，但扫描版 PDF 的 OCR 能力会受限。

## 项目结构（建议理解路径）

```text
book_translator_gui.pyw   # 主 GUI 入口
translation_engine.py     # 翻译引擎
file_processor.py         # 多格式读取 / 分段 / OCR 回退
config_manager.py         # 配置管理
app_paths.py              # 用户级运行时目录
web_importer.py           # URL 导入
start.bat                 # Windows 启动脚本
run_all_tests.bat         # 旧版手工测试入口
tests/                    # 新增的基础 pytest 冒烟测试
```

## 运行时文件

项目已经把大多数运行时数据迁移到用户配置目录，而不是源码仓库目录，例如：

- 配置文件
- 翻译缓存
- 批量任务缓存
- 备份目录
- 本地数据库

请不要把这些运行时文件重新提交进仓库。

## 测试

### 轻量冒烟测试

```bash
py -m pytest
```

### 旧版手工测试脚本

仓库仍保留了基于 `.bat` 和脚本串联的测试方式：

```bash
run_all_tests.bat
```

它更适合本地人工验证，不等价于完整自动化测试。

## 开发建议

当前项目功能较多，后续建议优先做这些事情：

1. 继续拆分 `book_translator_gui.pyw`
2. 把 GUI 逻辑与业务逻辑进一步解耦
3. 补充更多针对非 GUI 模块的自动化测试
4. 为导出、在线搜索、社区分享增加更稳定的集成测试
5. 建立发布说明与版本变更日志

## 已知现状

- 仓库历史中仍存在较多阶段性说明文件与旧测试脚本
- GUI 主文件体量较大，维护成本较高
- 一些功能依赖外部服务或本地系统组件，不能在纯 Python 环境下完全覆盖

## License

当前仓库未看到明确的开源许可证声明。若准备公开协作，建议补充 LICENSE 文件。
