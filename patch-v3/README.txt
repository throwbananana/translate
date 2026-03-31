# translate 升级修复包 v3

这个包改用**脚本修复**，不再依赖 `git apply`。

## 用法

在仓库根目录执行：

```powershell
Expand-Archive .\translate-upgrade-fix-bundle-v3.zip -DestinationPath .\patch-v3 -Force
py .\patch-v3\apply_translate_fix_bundle_v3.py .
py -m pytest tests/test_config_manager.py tests/test_gui_structure.py
```

如果你还没安装 pytest：

```powershell
py -m pip install -r requirements-dev.txt
py -m pytest tests/test_config_manager.py tests/test_gui_structure.py
```

## 这次会做什么

1. 修复 `book_translator_gui.pyw` 里 `open_admin_audit` 错误嵌套的问题  
2. 修复管理员“未启用”提示里的字符串换行问题  
3. 给 AI 元数据自动识别加一个 JSON 提取辅助方法，并替换原来的脆弱正则提取逻辑  
4. 新增 `tests/test_gui_structure.py`，做最小 GUI 结构烟雾测试  
5. 自动备份被改动的文件为 `*.bak_v3`
