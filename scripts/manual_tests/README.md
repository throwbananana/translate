# 手工测试脚本

这里存放需要人工观察、真实 API、GUI、本地模型或系统组件参与的验证脚本。

约定：

- 不纳入默认 `pytest` 或 CI
- 所有 API Key 一律通过环境变量读取
- 输出文件默认写入仓库根目录下的 `manual_outputs/`
- 根目录旧 `test_*.py` 目前保留为兼容入口，实际会转发到这里

建议环境变量：

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
