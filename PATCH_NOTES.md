# translate 升级完善补丁包（当前主分支定向）

这个补丁包针对当前仓库状态做了 3 组修复：

1. `0001-book-translator-gui-admin-audit-hotfix.patch`
   - 修复 `open_admin_audit()` 被错误嵌套进 `open_community_upload()` 的问题
   - 修复管理员未启用提示里的字符串换行，避免 GUI 语法错误
   - 恢复社区管理按钮可正常绑定类方法

2. `0002-book-translator-gui-json-hardening.patch`
   - 新增 `_extract_first_json_object()`
   - 提升 AI 自动识别书籍元数据时的 JSON 提取容错
   - 兼容 markdown 代码块里的 JSON

3. `0003-tests-gui-structure-smoke.patch`
   - 新增 `tests/test_gui_structure.py`
   - 用 `py_compile` 防止 GUI 再次引入语法错误
   - 用 AST 校验关键方法确实是 `BookTranslatorGUI` 的直接方法，防止再次被错误嵌套

## 推荐应用顺序

```powershell
git apply 0001-book-translator-gui-admin-audit-hotfix.patch
git apply 0002-book-translator-gui-json-hardening.patch
git apply 0003-tests-gui-structure-smoke.patch
pytest tests/test_config_manager.py tests/test_gui_structure.py
```

## 如果 0001 因为 GUI 大文件偏移而失败

可改用包内的 `fix_book_translator_gui_admin_audit.py`：

```powershell
py .\fix_book_translator_gui_admin_audit.py .\book_translator_gui.pyw
```

它会：
- 备份原文件为 `book_translator_gui.pyw.bak`
- 自动修复 `open_admin_audit` 缩进与字符串问题

## 说明

这次补丁故意保持“小补丁、低风险”，没有做大规模重构，目的是优先让当前仓库恢复到：
- GUI 可启动
- 社区页不回归
- AI 元数据自动识别更稳
- 测试能拦住同类错误
