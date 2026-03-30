# 修复后的补丁包使用说明

上一个包里的 `0001` patch 格式损坏，请改用这个修复版。

## Windows

```bat
apply_all_patches_fixed.bat
```

## Linux / macOS / Git Bash

```bash
chmod +x apply_all_patches_fixed.sh
./apply_all_patches_fixed.sh
```

## 单文件 git am

```bash
git am translate-upgrade-series-0001-0009-fixed.mbox
```
