# 安全单补丁使用说明（已修复）

当前仓库里原先引用的 `translate-safe-upgrade-single.patch` 并不存在，  
因此这里统一改为使用真实存在的修复版补丁：

- `0001-project-hardening-readme-deps-tests-ci-repaired.patch`

这是一份标准 unified diff / mailbox-style patch，优先使用 `git apply`。  
只有在你自己重新从真实提交导出 `.mbox` 后，才建议用 `git am`。

## 重要说明

如果你是在 `throwbananana/translate` 当前 `main` 分支里执行这些命令，  
补丁**大概率不会再 clean apply**，因为仓库当前已经包含了其中大部分甚至全部改动。

这个补丁更适合：

- 用在较早的基线分支上
- 当作审阅材料
- 对照当前仓库手工迁移变更

## Windows

```bat
apply_safe_upgrade_patch.bat
```

## 手工命令

```bash
git apply --check 0001-project-hardening-readme-deps-tests-ci-repaired.patch
git apply 0001-project-hardening-readme-deps-tests-ci-repaired.patch
py -m pip install -r requirements.txt
py -m pip install -r requirements-dev.txt
py -m pytest -q
```

## 成功后检查

```bash
git status
py -m pytest -q
```

## 如果 `git apply --check` 失败

常见原因：

1. 当前代码已经包含这些修改
2. 目标分支和补丁生成时的上下文不一致
3. 你真正需要的是从真实提交重新导出的 patch / mbox

如果你要继续维护 patch 分发物，建议下一步直接从真实 Git 提交重新执行：

```bash
git format-patch
```
