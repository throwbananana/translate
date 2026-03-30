# translate 升级优化补丁包

包含内容：

1. `0001-translation-engine-provider-readiness.patch`
   - 仅把“已正确配置”的 provider 暴露给可用列表。
   - 未配置完成时返回更清晰的错误，而不是误判为可用。

2. `0002-config-manager-security-env-overrides.patch`
   - 新增 `security.admin_password` 默认配置。
   - 支持环境变量覆盖：
     - `BOOK_TRANSLATOR_ADMIN_PASSWORD`
     - `ZLIBRARY_EMAIL`
     - `ZLIBRARY_PASSWORD`
     - `ZLIBRARY_COOKIE`
     - `ZLIBRARY_DOMAIN`
     - `ANNAS_ARCHIVE_DOMAIN`
   - 新增 `get_admin_password()` 辅助方法。

3. `0003-book-translator-gui-fix-ai-metadata-and-admin-auth.patch`
   - 修复社区上传页中 AI 自动识别元数据调用错误接口的问题。
   - 新增通用文本生成辅助方法，复用现有解析 API。
   - 管理员入口不再使用硬编码密码 `admin`，改为读取配置或环境变量，并使用 `hmac.compare_digest()` 校验。

4. `0004-tests-and-gitignore.patch`
   - 扩展 `ConfigManager` 环境变量覆盖测试。
   - 新增 `TranslationEngine` provider 就绪性测试。
   - `.gitignore` 补充 `server_data/` 与 `*.mbox`。

建议应用顺序：

```bash
git apply 0001-translation-engine-provider-readiness.patch
git apply 0002-config-manager-security-env-overrides.patch
git apply 0003-book-translator-gui-fix-ai-metadata-and-admin-auth.patch
git apply 0004-tests-and-gitignore.patch
```

`0003` 是针对大体量 GUI 文件的定点上下文补丁。建议优先用 `git apply --reject 0003-book-translator-gui-fix-ai-metadata-and-admin-auth.patch`，若出现少量 `.rej`，按补丁里的函数名搜索后手工套用即可。
