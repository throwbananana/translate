# `throwbananana/translate` 项目审查、修复与重构总方案

> 本文汇总了此前对项目的整体代码审查、问题诊断、修复建议、PR 拆分计划、测试/CI 方案、架构拆分建议，以及 README 结构建议，整理成一份可直接保存/分发的 Markdown 文档。

---

## 1. 项目总体判断

### 1.1 一句话结论

这是一个**功能很完整、产品方向清晰**的桌面端书籍翻译工具，但当前代码库仍带有明显的“持续叠功能长出来”的痕迹：  
**功能强，但主 GUI 过重，职责混杂，局部实现规则不一致，工程收口不足。**

### 1.2 功能侧评价

项目已经具备以下能力：

- 支持多种输入格式：TXT / Markdown / PDF / EPUB / DOCX / RTF
- 支持多种翻译 Provider：Gemini / OpenAI / Claude / DeepSeek / LM Studio / 自定义兼容 OpenAI API
- 支持自定义本地模型
- 支持翻译记忆（TM）
- 支持术语表管理与智能提取
- 支持失败段落识别 / 重试 / 手工修正
- 支持批量处理
- 支持双栏对照编辑
- 支持解析讲解
- 支持在线书城 / 社区图书馆
- 支持 TXT / DOCX / EPUB / 有声书导出

### 1.3 综合评分（建议性）

- **产品/功能层面：7.5 / 10**
- **代码结构层面：5.5 / 10**
- **工程化层面：5 / 10**

---

## 2. 主要优点

### 2.1 `translation_engine.py` 的方向是对的

引擎层已经做了比较合理的抽象，承载了这些职责：

- provider 抽象
- 翻译记忆调用
- 术语表注入
- 质量评估
- 重试与 fallback

这是项目里最值得继续巩固的一层。

### 2.2 `file_processor.py` 功能较完整

文件处理器支持：

- TXT 编码自动检测
- PDF：`pdfplumber` 优先，`PyPDF2` 回退
- PDF OCR 回退
- EPUB 文本与图片处理
- DOCX 文本提取
- Markdown / RTF 支持
- 文本分段与语言粗检测

说明项目已经不是“只能翻 TXT 的小工具”。

### 2.3 `config_manager.py` 已有工程化基础

配置管理已经包含：

- 用户目录配置
- 备份与恢复
- 环境变量覆盖
- 版本迁移
- 轻量敏感字段编码

这为后续收口打下了基础。

---

## 3. 当前最主要的问题

### 3.1 `book_translator_gui.pyw` 过大，职责混杂

主 GUI 文件当前同时承担了：

- 主窗口
- API 配置
- 文件加载
- 翻译流程编排
- 批量任务
- 失败段落修复
- 解析流程
- 在线搜索
- 社区图书馆
- 上传分享
- 管理员入口
- 导出功能
- 主题切换

它已经不只是 view，而是混合了：

- view
- controller
- workflow orchestration
- 一部分 service / adapter

### 3.2 LM Studio / 本地模型规则不一致

项目里曾同时存在两套规则：

- 翻译引擎层：`lm_studio` 可用条件是 `base_url + model`
- GUI 层：某些地方又把它当成“必须有 API key”

这种分叉会导致：

- GUI 拦住本应可用的本地模型
- `sync_engine_config()` 漏掉本地 provider
- fallback 行为和界面提示不一致

### 3.3 断点恢复对非纯文本文件存在真实 bug

正常加载文件走 `FileProcessor.read_file()`，  
但恢复缓存时曾直接：

```python
with open(file_path, 'r', encoding='utf-8') as rf:
    content = rf.read()
```

这会让 PDF / EPUB / DOCX 恢复失败或逻辑失真。

### 3.4 文件选择器与底层支持格式不一致

底层已支持：

- DOCX
- Markdown
- RTF

但 GUI 文件选择器一度仍只显示：

- TXT
- PDF
- EPUB

用户感知会与实际能力不一致。

### 3.5 仓库卫生和工程收口不足

存在的问题包括：

- 根目录堆放太多说明/补丁/临时文件
- 运行时产物与备份文件可能混入仓库
- 缺乏明确的 LICENSE
- 测试结构虽然已经开始规范化，但历史测试脚本仍较散

### 3.6 “加密”表述需要谨慎

`config_manager.py` 中敏感字段更多是**轻量编码/混淆**，而非真正的安全加密。  
文案上不应把它当成强安全能力宣传。

---

## 4. 最高优先级修复（P0）

以下建议是“先止血”的部分，建议最先做。

### 4.1 修复恢复流程统一走 `FileProcessor`

**目标：** 所有从路径重新读取内容的流程都统一走 `FileProcessor.read_file()`。

应修位置：

- `try_resume_cached_progress()`

不要再直接用 `open(..., encoding='utf-8')` 读取 PDF / EPUB / DOCX。

---

### 4.2 统一 Provider 配置校验

**目标：** GUI 层不再单独维护与引擎冲突的 provider 规则。

至少要统一这些点：

- `start_translation()`
- `retry_failed_segment()`
- `open_api_config()` 的测试连接
- `sync_engine_config()`
- API 状态显示

---

### 4.3 修复 `sync_engine_config()` 对 `lm_studio` 的误伤

不要再统一写成：

```python
if not cfg.get('api_key'):
    continue
```

应按 provider 类型判断：

- 云端 provider：需要 API key + model
- `lm_studio`：需要 `base_url + model`
- `custom`：建议 `api_key + base_url + model`
- 自定义本地模型：需要 `base_url + model_id`

---

### 4.4 文件对话框复用 `FileProcessor.get_file_filter()`

GUI 不应再自己维护一套格式列表。  
应让文件选择器直接复用底层提供的过滤器。

---

### 4.5 修复搜索树重建里的变量引用问题

`_refresh_search_tree_grouped()` 曾存在父节点插入时引用未定义 `res` 的问题。  
应改为使用组内第一个元素的 `source`。

---

## 5. 中优先级修复（P1）

### 5.1 抽统一的 provider 校验 helper

建议引入统一 helper，例如：

- `_provider_ready_for_gui()`
- `_ensure_provider_ready_or_prompt()`

后续再进一步下沉到 `provider_utils.py`。

### 5.2 统一“内容进入工作区”的入口

建议引入：

- `load_content_into_workspace(...)`

统一覆盖：

- 打开本地文件
- URL 导入
- 剪贴板导入
- 社区下载导入
- 批量任务加载
- 断点恢复

### 5.3 统一状态清理

建议抽：

- `reset_translation_state()`
- `reset_analysis_state()`

避免不同入口分别手动清理状态字段。

### 5.4 失败段落纯逻辑下沉

建议把这类逻辑移出 GUI：

- 译文是否不完整
- 失败段落列表构建
- 自动重试后的占位处理
- 手工修正应用

---

## 6. 仓库与工程化收口（P2）

### 6.1 清理运行时产物和根目录杂项

建议移除或忽略：

- `translation_cache.json`
- `batch_tasks.json`
- `translation_memory.db`
- 配置备份目录
- 下载目录
- 其他本地运行产物

### 6.2 补 `.gitignore`

建议至少包含：

```gitignore
.pytest_cache/
.coverage
coverage.xml
htmlcov/
test-results/
__pycache__/
*.pyc
```

### 6.3 补 License / Changelog / 发布说明

最少补：

- `LICENSE`
- `CHANGELOG.md`
- README 中的版本/发布说明

---

## 7. 逐函数修改建议（第一阶段可直接落地）

> 这一节汇总了此前给出的“逐函数替换方案”的核心要点。

### 7.1 建议新增的 GUI helper

建议在 `BookTranslatorGUI` 内加入：

- `_read_content_for_path(self, filepath)`
- `_provider_ready_for_gui(self, api_type)`
- `_ensure_provider_ready_or_prompt(self, api_type)`
- `_init_docx_handler_if_needed(self, filepath)`

### 7.2 `get_current_api_type()`

改为直接返回：

```python
return self.get_translation_api_type()
```

避免继续使用过时的旧映射。

### 7.3 `browse_file()`

改为：

- 使用 `self.file_processor.get_file_filter()`
- 不再手写 `*.txt *.pdf *.epub`

### 7.4 `load_file_content()`

应通过统一入口读取文件内容，并统一做：

- `current_text`
- `text_signature`
- TOC
- DOCX handler
- 大文件预览状态
- 成本估算

### 7.5 `try_resume_cached_progress()`

恢复时必须：

- 通过 `_read_content_for_path()` 或 `FileProcessor.read_file()`
- 不再直接文本打开文件
- 恢复后补做 TOC 初始化、DOCX handler 初始化

### 7.6 `sync_engine_config()`

应按 provider 类型判断可用性，而不是统一看 `api_key`。

### 7.7 `start_translation()`

不要再手写 provider 配置规则，直接通过统一 helper 校验。

### 7.8 `retry_failed_segment()`

同上，直接复用统一 provider 校验 helper。

### 7.9 `open_api_config()` 中的 `test_connection()` / `save_config()`

- `lm_studio` 允许空 API key
- 需要 `base_url + model`
- 其他 provider 按各自规则校验

### 7.10 `_refresh_search_tree_grouped()`

父节点来源不要再引用未定义变量，应从组内第一项取 source。

---

## 8. 第一阶段建议测试文件

推荐新增并保留这些测试：

### 8.1 `tests/test_recent_fixes.py`

覆盖：

- `get_current_api_type()` 与自定义本地模型
- `lm_studio` 不要求真实 API key
- `sync_engine_config()` 保留 `lm_studio`
- `browse_file()` 复用 `FileProcessor.get_file_filter()`
- `try_resume_cached_progress()` 走 `FileProcessor.read_file()`
- `_refresh_search_tree_grouped()` 不再引用未定义变量

### 8.2 `tests/test_file_filters.py`

覆盖：

- 文件过滤器中包含 Markdown
- 若支持 DOCX，则过滤器中也包含 DOCX

---

## 9. GitHub Actions / CI 方案

### 9.1 最小可用版

建议 workflow：

- Python 3.11 / 3.12
- 安装 `requirements.txt` + `requirements-dev.txt`
- 跑 focused tests
- 可选安装：
  - `tesseract-ocr`
  - `poppler-utils`

### 9.2 完整版 CI 能力

建议包括：

- Ruff 静态检查
- pytest + coverage
- 覆盖率报告 artifact 上传
- pytest 日志失败时上传

### 9.3 推荐的 CI 工作流

建议包含两个 job：

- `lint`
- `test`

并上传：

- `pytest.log`
- `coverage.xml`

---

## 10. PR 拆分总路线图

---

## 11. PR 1：统一 Provider 校验 + 引擎测试

### 11.1 新增 `provider_utils.py`

负责：

- `validate_builtin_provider(...)`
- `validate_custom_local_model(...)`
- `provider_ready(...)`
- `provider_error_message(...)`
- `list_ready_builtin_providers(...)`
- `list_ready_custom_local_models(...)`

### 11.2 GUI 接入

`book_translator_gui.pyw` 中：

- `_provider_ready_for_gui()` 改为转调 `provider_utils.py`
- `sync_engine_config()` 不再自己定义 provider 规则

### 11.3 建议测试

新增：

- `tests/test_provider_utils.py`
- `tests/test_translation_engine_providers.py`

覆盖：

- `lm_studio` 的 ready 规则
- custom local model ready 规则
- fallback provider 选择
- `create_engine_with_config()` 行为

---

## 12. PR 2：统一工作区加载入口

### 12.1 新增 / 抽取方法

建议在 GUI 中新增：

- `reset_translation_state()`
- `reset_analysis_state()`
- `load_content_into_workspace(...)`

### 12.2 统一覆盖这些入口

- `load_file_content()`
- `_load_imported_content()`
- `_load_downloaded_book()`
- `browse_file()`
- `process_next_batch_file()`
- `try_resume_cached_progress()`

### 12.3 建议测试

新增：

- `tests/test_workspace_loading.py`

覆盖：

- 从纯文本内容装入工作区
- 从路径读文件装入工作区
- 状态字段与 UI 更新是否统一

---

## 13. PR 3：下沉失败段落与翻译复核逻辑

### 13.1 新增 `translation_review.py`

负责：

- `is_translation_incomplete(...)`
- `build_failed_segments(...)`
- `verify_and_retry_segments(...)`
- `apply_manual_translation(...)`

### 13.2 GUI 侧处理

GUI 保留：

- 用户选中哪一段
- 调用 service
- 更新界面
- 把人工修正写回 TM

### 13.3 建议测试

新增：

- `tests/test_translation_review.py`

覆盖：

- 空译文 / 错误标记 / 占位文本判定
- 中译英/英译中的粗完整性判断
- 重试成功 / 重试失败时的行为
- 手工修正应用

---

## 14. PR 4：拆 `GlossaryEditorDialog` 和在线书城 / 社区图书馆

### 14.1 新增 UI 模块

- `ui/glossary_dialog.py`
- `ui/library_panel.py`

### 14.2 主 GUI 改为装配

- `open_glossary_editor()` 调 `GlossaryEditorDialog`
- `setup_search_tab()` 改为装配 `LibraryPanel`

### 14.3 UI 层职责

这些 panel 只负责：

- 布局
- 控件
- 绑定 callback

不直接持有核心业务逻辑。

### 14.4 建议测试

新增：

- `tests/test_ui_imports.py`

至少覆盖导入 smoke test。

---

## 15. PR 5：拆失败段落页与解析页

### 15.1 新增 UI 模块

- `ui/failed_segments_panel.py`
- `ui/analysis_panel.py`

### 15.2 主 GUI 改动

GUI 继续持有状态，但通过 panel 访问控件。

例如：

- `self.failed_panel.failed_listbox`
- `self.analysis_panel.analysis_text`

### 15.3 建议测试

继续扩展 `tests/test_ui_imports.py`，至少覆盖这两个 panel 的导入 smoke test。

---

## 16. PR 6：拆翻译工作台表单层

### 16.1 新增目录与模块

```text
ui/workstation/
├─ file_panel.py
├─ api_panel.py
├─ progress_panel.py
└─ action_bar.py
```

### 16.2 拆出去的块

- 文件选择区
- API 配置区
- 进度区
- 操作按钮区

### 16.3 主 GUI 保留

保留：

- 状态
- callback
- 工作流程协调

### 16.4 建议测试

新增：

- `tests/test_workstation_panel_imports.py`

---

## 17. PR 7：拆内容显示区

### 17.1 新增 `ui/content_notebook.py`

容纳：

- 原文页
- 译文页
- 双栏对照页

### 17.2 TOC 暂不下沉

TOC 与滚动定位耦合较高，建议晚一轮再拆。

### 17.3 主 GUI 的过渡做法

为了降低改动面，建议先保留兼容映射：

- `self.notebook = self.content_notebook.notebook`
- `self.original_text = self.content_notebook.original_text`
- `self.translated_text_widget = self.content_notebook.translated_text_widget`
- `self.comp_source_text = self.content_notebook.comp_source_text`
- `self.comp_target_text = self.content_notebook.comp_target_text`

### 17.4 建议测试

新增：

- `tests/test_content_notebook_imports.py`

---

## 18. 推荐的最终目录结构

```text
translate/
├─ book_translator_gui.pyw
├─ provider_utils.py
├─ translation_review.py
├─ translation_engine.py
├─ file_processor.py
├─ config_manager.py
├─ app_paths.py
├─ translation_memory.py
├─ glossary_manager.py
├─ online_search.py
├─ book_hunter.py
├─ web_importer.py
├─ cost_estimator.py
├─ docx_handler.py
├─ audio_manager.py
├─ smart_glossary.py
├─ community_manager.py
├─ cloud_upload.py
├─ format_converter.py
├─ tm_editor.py
│
├─ ui/
│  ├─ __init__.py
│  ├─ glossary_dialog.py
│  ├─ library_panel.py
│  ├─ failed_segments_panel.py
│  ├─ analysis_panel.py
│  ├─ content_notebook.py
│  └─ workstation/
│     ├─ __init__.py
│     ├─ file_panel.py
│     ├─ api_panel.py
│     ├─ progress_panel.py
│     └─ action_bar.py
│
├─ tests/
│  ├─ test_recent_fixes.py
│  ├─ test_file_filters.py
│  ├─ test_provider_utils.py
│  ├─ test_translation_engine_providers.py
│  ├─ test_workspace_loading.py
│  ├─ test_translation_review.py
│  ├─ test_ui_imports.py
│  ├─ test_workstation_panel_imports.py
│  └─ test_content_notebook_imports.py
│
├─ .github/workflows/ci.yml
├─ requirements.txt
├─ requirements-dev.txt
├─ pytest.ini
├─ .ruff.toml
├─ .gitignore
└─ README.md
```

---

## 19. 建议的架构关系图

### 19.1 模块关系

```text
BookTranslatorGUI
├─ ConfigManager
├─ TranslationEngine
├─ FileProcessor
├─ TranslationMemory
├─ GlossaryManager
├─ OnlineSearchManager
├─ BookHunter
├─ CommunityManager
├─ WebImporter
│
├─ FilePanel
├─ ApiPanel
├─ ProgressPanel
├─ ActionBar
├─ ContentNotebook
├─ FailedSegmentsPanel
├─ AnalysisPanel
└─ LibraryPanel
```

### 19.2 依赖方向

推荐保持：

```text
UI Panels
   ↓ callback
BookTranslatorGUI
   ↓
Service Modules
(provider_utils / translation_review / translation_engine / file_processor / ...)
```

应避免：

```text
UI Panel → 直接 import translation_engine / config_manager / TM / community_manager
```

否则会再次长出新的“超级 GUI 文件”。

---

## 20. 主窗口最终应保留的核心职责

### 20.1 适合继续留在 `book_translator_gui.pyw` 的内容

- 应用初始化
- 全局状态
- UI 装配
- callback 路由
- 跨模块协调

### 20.2 不适合继续往主 GUI 里堆的内容

- 大量控件布局
- Provider 校验规则
- 失败段落纯业务逻辑
- 文件读取路径分叉
- 单纯的 view 组件

---

## 21. 未来可以继续优化的方向

### 21.1 引入 controllers

后续可以考虑：

```text
controllers/
├─ translation_controller.py
├─ analysis_controller.py
├─ workspace_controller.py
└─ library_controller.py
```

### 21.2 用 dataclass 管理运行态状态

例如：

- `TranslationState`
- `AnalysisState`
- `WorkspaceState`

这样 `reset_translation_state()` / `reset_analysis_state()` 会更自然。

### 21.3 继续扩大测试覆盖

优先方向：

- `ConfigManager`
- `TranslationEngine`
- `translation_review`
- `provider_utils`
- 工作区加载入口
- UI smoke tests

---

## 22. README 建议结构

建议 README 至少包含：

1. 项目简介
2. 功能概览
3. 安装要求
4. 快速开始
5. 支持的文件格式
6. 支持的翻译 Provider
7. 配置说明
8. 核心功能说明
9. 项目结构与架构说明
10. 运行逻辑概览
11. 测试
12. CI
13. 开发说明
14. FAQ
15. Roadmap
16. 已知限制
17. 贡献指南
18. License
19. 致谢

---

## 23. README 可直接使用的“项目结构与架构说明”建议文案

> 可放入 `README.md` 中。

### 23.1 项目结构

- `book_translator_gui.pyw`：主程序入口，负责装配 UI 与协调流程
- `translation_engine.py`：翻译引擎
- `file_processor.py`：文件处理
- `provider_utils.py`：Provider 校验
- `translation_review.py`：失败段落复核
- `ui/`：各类面板与对话框
- `tests/`：pytest 测试

### 23.2 架构分层

- 主窗口层：装配与协调
- 服务模块层：业务逻辑与可复用逻辑
- UI 面板层：布局、控件、回调绑定

### 23.3 开发原则

- 新功能优先写到服务模块
- 所有文件加载统一入口
- GUI 不继续定义业务规则
- 纯逻辑优先补测试

---

## 24. 推荐的提交与合并方式

### 24.1 分支建议

```bash
git checkout -b fix/resume-provider-ci
```

或后续 PR 分支：

- `refactor/provider-rules`
- `refactor/workspace-loader`
- `refactor/review-logic`
- `refactor/ui-panels`

### 24.2 推荐的提交风格

- `fix: ...`
- `refactor: ...`
- `test: ...`
- `ci: ...`
- `docs: ...`

### 24.3 本地提交前建议执行

```bash
ruff check .
pytest -q
```

---

## 25. 当前最推荐的实施顺序

### 第一阶段（先稳定）
1. 修恢复流程
2. 统一 provider 规则
3. 修文件过滤器
4. 修 `_refresh_search_tree_grouped()`
5. 补 focused tests
6. 上最小 CI

### 第二阶段（再收口）
1. `provider_utils.py`
2. `load_content_into_workspace(...)`
3. `translation_review.py`
4. `ConfigManager` 测试
5. 清理仓库结构

### 第三阶段（拆 GUI）
1. `GlossaryEditorDialog`
2. `LibraryPanel`
3. `FailedSegmentsPanel`
4. `AnalysisPanel`
5. `workstation/*`
6. `ContentNotebook`

---

## 26. 最后建议

如果只能先做一件事，建议优先做：

> **统一 provider 规则 + 修恢复流程 + 上 focused tests**

因为这三件事最能立刻降低：

- 实际使用 bug
- GUI / engine 规则分叉
- 后续回归风险

如果拆 GUI 之前不先把这些打稳，后面重构会更痛苦。

---

## 27. README 完整目录提纲（可直接用于重写 README）

### 27.1 建议提纲

1. 项目简介
2. 功能概览
3. 界面预览（可选）
4. 适用场景
5. 安装要求
6. 快速开始
7. 支持的文件格式
8. 支持的翻译 Provider
9. 配置说明
10. 核心功能说明
11. 项目结构与架构说明
12. 运行逻辑概览
13. 测试
14. CI
15. 开发说明
16. FAQ
17. Roadmap
18. 已知限制
19. 贡献指南
20. License
21. 致谢

### 27.2 说明

README 中建议重点补上：

- 配置文件位置说明
- 环境变量覆盖说明
- 工作区加载统一逻辑说明
- Provider 校验规则说明
- 测试与 CI 使用方式

---

## 28. 备注

本文档基于此前连续审查与分阶段重构建议整理而成，适合：

- 自己继续分 PR 改造
- 作为仓库内 `docs/refactor-plan.md`
- 作为团队同步文档
- 作为后续 README / Roadmap / Issue 的来源文档
