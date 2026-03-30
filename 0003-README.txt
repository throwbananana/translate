0003 修复说明
================

原始的 0003-book-translator-gui-fix-ai-metadata-and-admin-auth.patch 不是一个有效的 unified diff，
所以 git apply 会报：No valid patches in input。

这里提供的是一个等价的自动修复脚本：
- 0003-book-translator-gui-fix.py

它会对当前目录下的 book_translator_gui.pyw 做以下修改：
1. 增加 import hmac
2. 插入 generate_text_with_selected_api() 辅助方法
3. 修复 AI 自动识别书籍元数据时，对 translation_engine.translate() 的错误调用
4. 强化 JSON 提取逻辑
5. 去掉硬编码管理员密码，改为读取 ConfigManager 中的 security.admin_password

使用方法（PowerShell）
----------------------
py .\0003-book-translator-gui-fix.py

如果你的 GUI 文件不在当前目录：
py .\0003-book-translator-gui-fix.py .\book_translator_gui.pyw

脚本会自动生成一个 .bak.YYYYMMDD_HHMMSS 备份文件。
