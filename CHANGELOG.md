# Changelog

## Unreleased

- 新增 `controllers.translation_run_config`，为后台翻译线程提供不可变运行配置快照，后续用于移除 worker 对 Tk 变量的直接读取
- 新增 `controllers.run_guard`，为停止翻译后的迟到 worker 结果提供统一拒收机制
- 新增 `controllers.gui_translation_adapter`，集中处理 GUI/Tk 变量读取、guarded run 启动和 stale worker UI 写回过滤
- 新增 `controllers.batch_task`，统一批量任务状态、错误记录、输出路径和旧队列兼容转换
- 新增 `providers/` adapter 基础层，包含统一 request/response/error 类型、OpenAI-compatible provider timeout 处理、从现有 APIConfig/custom-local-model 设置构造 adapter 的工厂函数，以及兼容 `translation_engine.py` 当前 tuple 返回值的 engine bridge
- `translation_engine.py` 非流式 OpenAI / DeepSeek / LM Studio / custom-local 调用已接入 OpenAI-compatible adapter bridge，并新增 `timeout_seconds` 配置传递
- 新增 `docs/upgrade-plan.md`，记录稳定性、controller 下沉、Provider Adapter、批量任务与发布化路线
- 新增 `tests/test_translation_run_config.py`、`tests/test_run_guard.py`、`tests/test_gui_translation_adapter.py`、`tests/test_batch_task.py`、`tests/test_provider_base.py`、`tests/test_openai_compatible_provider.py`、`tests/test_openai_compatible_factory.py`、`tests/test_engine_bridge.py` 与 `tests/test_translation_engine_adapter_bridge.py`，覆盖运行配置、停止保护、GUI adapter、批量任务状态、Provider timeout/factory 默认值、engine bridge 和 TranslationEngine 接入行为
- 新增 `scripts/manual_tests/`，迁移旧手工测试脚本并保留根目录兼容入口
- 移除手工脚本和工具脚本中的明文 Gemini API Key，统一改为环境变量读取
- 新增 `run_manual_tests.bat`、GitHub Actions CI、开发依赖与 pytest 标记配置
- 补充仓库安全与协作文档，并更新 README 中的测试与安全说明
- 新增 `provider_utils.py` 与 `translation_review.py`，统一 provider 校验、回退选择与失败段落复核逻辑
- GUI 工作区加载与断点恢复统一走 `FileProcessor` / `load_content_into_workspace()`，修复非纯文本文件恢复问题
- 文件选择器与批量导入过滤器改为复用 `FileProcessor.get_file_filter()`
- 修复搜索结果分组刷新时的来源字段引用错误
- CI 测试 job 现在会输出 `coverage.xml` 和 `pytest.log` artifact
- 新增 `ui/` 组件模块，已拆出术语表对话框、失败段落页、解析页和内容显示区
- 在线书城页已拆到 `ui/library_panel.py`
- 主 GUI 的内容区与失败/解析页改为装配 `ui` 模块，保留原有状态与回调逻辑
- 工作台顶部的文件区 / API 配置区 / 进度区 / 操作按钮区已拆到 `ui/workstation/`
- 补充 `tests/test_translation_engine_providers.py`，覆盖 `create_engine_with_config()`、LM Studio 与自定义本地模型的 provider 行为
- 内容区左侧章节目录已拆到 `ui/toc_panel.py`
- 更新 `.gitignore`、README 与 CONTRIBUTING，补充重构状态说明并忽略 CI / 本地运行产物
