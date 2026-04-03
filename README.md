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
provider_utils.py        # Provider 可用性校验 / 回退选择
translation_review.py    # 失败段落复核与人工修正逻辑
file_processor.py         # 多格式读取 / 分段 / OCR 回退
config_manager.py         # 配置管理
app_paths.py              # 用户级运行时目录
web_importer.py           # URL 导入
ui/                       # 已拆分的对话框与内容面板组件
start.bat                 # Windows 启动脚本
run_all_tests.bat         # 兼容旧测试入口
run_manual_tests.bat      # 新版手工测试菜单
tests/                    # 自动化 pytest 测试
scripts/manual_tests/     # 真实 API / GUI / 人工验证脚本
manual_outputs/           # 手工测试输出目录（运行时生成）
```

## Provider 规则

- `LM Studio` 不要求真实 API Key，只要求 `Base URL + 模型名称` 可用
- 自定义本地模型要求 `Base URL + Model ID`
- 自定义兼容 OpenAI API 要求 `API Key + Base URL + 模型名称`
- GUI 与 `translation_engine.py` 现在共用 `provider_utils.py` 进行可用性校验和回退选择

## 工作区加载

- 本地文件、剪贴板、URL 导入、下载后导入、断点恢复现在统一走工作区加载入口
- 恢复断点时会统一通过 `FileProcessor.read_file()` 重新读取文件，避免 PDF / EPUB / DOCX 被误当成纯文本打开
- 文件选择器和批量导入过滤器复用 `FileProcessor.get_file_filter()`，不会再和底层支持格式脱节

## UI 拆分进度

- `GlossaryEditorDialog` 已迁移到 `ui/glossary_dialog.py`
- 在线书城页已迁移到 `ui/library_panel.py`
- 失败段落页已迁移到 `ui/failed_segments_panel.py`
- 解析页已迁移到 `ui/analysis_panel.py`
- 原文 / 译文 / 双栏对照内容区已迁移到 `ui/content_notebook.py`
- 章节目录侧边栏已迁移到 `ui/toc_panel.py`
- 工作台顶部的文件区 / API 配置区 / 进度区 / 操作按钮区已迁移到 `ui/workstation/`
- 主 GUI 仍负责状态与回调路由，UI 模块只负责布局和控件暴露

## 重构状态

- 方案中的第一阶段稳定性修复已经完成：provider 规则、工作区加载、断点恢复、文件过滤器、搜索树分组问题都已收口
- 第二阶段基础抽象已经完成：`provider_utils.py`、`translation_review.py`、统一工作区入口和 focused tests 已落地
- 第三阶段主要 UI 拆分已经完成：术语表、书城、失败段落、解析、内容区、目录侧栏、工作台顶部表单都已拆到 `ui/`
- 当前剩余更偏“后续优化”而非阻塞项，主要是继续把主 GUI 的流程协调逻辑下沉到 controller / state 对象，以及替换已弃用依赖

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

### 手工测试脚本

仓库保留了兼容旧入口的根目录脚本，也提供了新的手工测试目录：

```bash
run_all_tests.bat
run_manual_tests.bat
```

真实 API 相关脚本现在统一放在 `scripts/manual_tests/` 下，默认输出写入 `manual_outputs/`。

如需运行 Gemini 相关手工测试，请先设置环境变量：

```bash
set GEMINI_API_KEY=你的密钥
```

这些脚本适合本地人工验证，不等价于完整自动化测试，也不会进入默认 CI。

CI 会上传 `coverage.xml` 和 `pytest.log` 作为 artifact，便于排查线上失败。

## 安全约定

- 不要把 API Key、Token 或密码写进脚本和文档
- 手工测试统一通过环境变量读取密钥
- 运行时配置、数据库、备份与手工测试输出不应纳入 Git
- 更多说明见 `SECURITY.md`

## 开发建议

当前项目功能较多，后续建议优先做这些事情：

1. 继续把 `book_translator_gui.pyw` 的流程协调逻辑下沉到 controller / state 对象
2. 把在线搜索、社区分享、导出流程补成更稳定的集成测试
3. 逐步迁移 `PyPDF2` 到 `pypdf`
4. 逐步迁移 `google.generativeai` 到新的 `google.genai`
5. 清理根目录历史补丁、阶段性说明和旧脚本

## 已知现状

- 仓库历史中仍存在较多阶段性说明文件与旧测试脚本
- GUI 主文件体量较大，维护成本较高
- 一些功能依赖外部服务或本地系统组件，不能在纯 Python 环境下完全覆盖

## License

当前仓库未看到明确的开源许可证声明。若准备公开协作，建议补充 LICENSE 文件。
