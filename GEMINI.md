# Workspace Analysis: Book Translator GUI

Python 桌面应用（Tkinter）用于翻译 TXT/PDF/EPUB 书籍，支持 Gemini、OpenAI 以及任意兼容 OpenAI 协议的自定义接口。当前版本在云端 API 配额耗尽时，会自动切换到本地 LM Studio 模型（默认 qwen2.5-7b-instruct-1m @ http://127.0.0.1:1234/v1），无需浏览器或 Selenium。

## Project Overview

* **Type:** Python Desktop Application (GUI)
* **Primary Interface:** Tkinter
* **Core Function:** Automated document translation with large-file handling.
* **Key Dependencies:** `google-generativeai`, `openai`, `PyPDF2`, `ebooklib`, `beautifulsoup4`, `requests`.

## Key Files & Directories

### Application Core
* `book_translator_gui.pyw`: 主入口，包含 GUI、文件读取与翻译编排逻辑。
* `translator_config.json`: 保存 API/模型配置（含本地 `lm_studio` 默认段）。

### Launchers & Scripts
* `start.bat`：Windows 启动脚本。
* `run_all_tests.bat`: 运行测试脚本集合。

### Documentation
* `README.md`: 安装、特性、使用说明。
* `使用说明-请先看这个.txt`: 中文使用指南。
* `大文件处理说明.md`: 大文件预览/加载说明。

### Testing
包含多个测试脚本：
* `test_core_features.py`: 核心功能检查。
* `test_large_file.py`: 大文本/预览测试。
* `test_actual_translation.py`: 实际翻译冒烟测试。

## Building and Running

### Prerequisites
* Python 3.x
* 可选：LM Studio（用于本地备用翻译），需开启 OpenAI-Compatible Server

### Installation
```
pip install -r requirements.txt
```

### Execution
```
start.bat
# 或
python book_translator_gui.pyw
```

### Testing
```
run_all_tests.bat
```

## Current State
* **Version:** v2.3 (2025-12-24)
* **Recent Changes:**
  * **PDF 增强**: 集成 `pdfplumber` (排版保持) + `pdf2image`/`OCR` (扫描件支持)
  * **术语表管理**: 新增可视化编辑器 `GlossaryEditorDialog`
  * **界面升级**: 新增章节目录 (TOC) 侧边栏与点击跳转
  * **体验优化**: 批量任务队列持久化 (`batch_tasks.json`)
  * **核心**: 统一使用 `TranslationEngine`，支持多线程并发

