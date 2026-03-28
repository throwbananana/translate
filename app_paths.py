#! python
# -*- coding: utf-8 -*-
"""应用运行态路径工具。

统一管理用户级配置/缓存/数据库目录，避免把运行态文件写回源码仓库。
"""

from __future__ import annotations

import os
from pathlib import Path


APP_DIR_WINDOWS = "BookTranslator"
APP_DIR_POSIX = "book_translator"


def get_app_dir() -> Path:
    """返回用户级应用目录。"""
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / APP_DIR_WINDOWS
        return Path.home() / "AppData" / "Roaming" / APP_DIR_WINDOWS

    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / APP_DIR_POSIX

    return Path.home() / ".config" / APP_DIR_POSIX


def ensure_app_dir() -> Path:
    path = get_app_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_runtime_file(filename: str) -> Path:
    path = ensure_app_dir() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_backup_dir() -> Path:
    path = ensure_app_dir() / "config_backups"
    path.mkdir(parents=True, exist_ok=True)
    return path
