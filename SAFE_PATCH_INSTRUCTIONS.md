# 安全单补丁使用说明

这是一份标准 unified diff，不是 mailbox patch。
请使用 `git apply`，不要用 `git am`。

## Windows

```bat
apply_safe_upgrade_patch.bat
```

## 手工命令

```bash
git apply --check translate-safe-upgrade-single.patch
git apply translate-safe-upgrade-single.patch
py -m pip install -r requirements.txt
py -m pip install -r requirements-dev.txt
py -m pytest -q
```

## 成功后检查

```bash
git status
py -m pytest -q
```
