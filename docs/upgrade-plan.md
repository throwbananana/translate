# translate 优化升级计划

本计划把项目升级拆成可独立合并的小阶段，避免一次性重构 `book_translator_gui.pyw` 带来过高回归风险。

## 总目标

1. 稳定真实使用流程：停止翻译有效、API 不无限等待、批量任务不被弹窗阻塞。
2. 收口架构边界：GUI 只负责装配和事件路由，流程状态逐步下沉到 controller 层。
3. 提升可测试性：把纯配置、状态机、Provider 调用、工作区加载做成无 GUI 单元测试。
4. 准备发布化：清理历史补丁文件、补 License、补打包和手工验证说明。

## Phase 1：稳定翻译运行态

### 1.1 翻译运行配置快照

新增 `controllers.translation_run_config`，用于在主线程读取 Tk 变量后生成不可变配置快照，再传入后台翻译线程。

目标：后台线程不再直接读取 Tkinter 变量，降低线程安全风险。

当前已落地：

- `TranslationRunConfig`
- `coerce_translation_run_config(...)`
- 风格提示词集中映射
- 并发模式下自动关闭上下文判断
- Provider 默认 timeout 字段
- 对应单元测试 `tests/test_translation_run_config.py`

### 1.2 停止翻译保护

后续改动：

- 为每次翻译运行生成 `run_id`
- UI 写回前检查 `run_id` 是否仍是当前运行
- 点击停止后，迟到结果不得继续写入译文区
- 停止状态下只允许保存已完成段落，不覆盖用户手动修正

### 1.3 Provider timeout

后续改动：

- OpenAI-compatible / LM Studio / DeepSeek 增加统一 timeout
- Claude / Gemini 调用增加可控超时或外层超时保护
- timeout 错误归类为可展示错误，不直接卡死 GUI

## Phase 2：批量任务稳定化

目标：批量处理可无人值守运行。

计划：

- `load_file_content(filepath, silent=False)` 增加静默模式
- 批量模式调用 `silent=True`
- 批量任务状态统一为：`pending/loading/translating/exporting/done/failed/cancelled`
- 每个任务记录 `error`、`started_at`、`finished_at`、`output_path`
- 单个任务失败不阻断整个队列

## Phase 3：工作区加载下沉

目标：本地文件、URL、剪贴板、下载导入、断点恢复、批量载入统一入口。

计划新增：

```text
controllers/
└─ workspace_controller.py
```

核心结果对象：

```python
WorkspaceLoadResult(
    title,
    filepath,
    content,
    char_count,
    word_count,
    is_large_file,
    text_signature,
    cost_info,
)
```

GUI 只负责把结果渲染到控件。

## Phase 4：Provider Adapter

目标：Provider 校验和 Provider 调用都统一。

计划新增：

```text
providers/
├─ base.py
├─ openai_compatible.py
├─ gemini_provider.py
├─ claude_provider.py
└─ custom_provider.py
```

统一错误类型：

- `ProviderTimeoutError`
- `ProviderQuotaError`
- `ProviderAuthError`
- `ProviderResponseError`

## Phase 5：文件处理增强

计划：

- TXT 编码检测引入 `charset-normalizer` 或等价策略
- `latin1` 只作为最后 fallback
- RTF 改成可选依赖处理，避免正则误删内容
- OCR 组件缺失时给出明确 GUI 提示
- OCR 测试放入 optional integration workflow

## Phase 6：在线书源插件化

目标：主翻译功能与在线书源隔离。

计划：

- 默认不启用争议书源
- 下载能力拆成显式开关
- README 明确仅用于用户有权访问的资源
- 在线搜索失败不得影响主翻译工作台

## Phase 7：仓库清理与发布规范

计划：

- 清理 tracked 的 `.mbox`、`.bak`、patch bundle、旧修复脚本
- 补 `LICENSE`
- `project_review_and_refactor_plan.md` 移动到 `docs/`
- 补 `docs/architecture.md`
- 补 `docs/manual-testing.md`
- 增加打包说明与启动前环境检查

## 推荐 PR 顺序

1. `refactor: add translation run config snapshot`
2. `fix: guard stopped translation writes`
3. `fix: add provider timeout handling`
4. `fix: make batch loading silent`
5. `refactor: extract workspace controller`
6. `refactor: add provider adapters`
7. `fix: improve file decoding and OCR diagnostics`
8. `chore: clean repository and add license`
