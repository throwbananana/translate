# Changelog

## Unreleased

- 新增 `scripts/manual_tests/`，迁移旧手工测试脚本并保留根目录兼容入口
- 移除手工脚本和工具脚本中的明文 Gemini API Key，统一改为环境变量读取
- 新增 `run_manual_tests.bat`、GitHub Actions CI、开发依赖与 pytest 标记配置
- 补充仓库安全与协作文档，并更新 README 中的测试与安全说明
