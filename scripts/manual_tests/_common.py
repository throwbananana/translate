#! python
# -*- coding: utf-8 -*-
"""手工测试通用辅助函数。"""

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUTPUT_DIR = REPO_ROOT / "manual_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def require_env(name: str) -> str:
    """读取必需环境变量。"""
    value = os.getenv(name, "").strip()
    if value:
        return value
    raise RuntimeError(f"缺少环境变量: {name}。请先在当前终端设置后再运行该手工测试。")


def resolve_repo_path(*parts: str) -> Path:
    """拼出仓库内路径。"""
    return REPO_ROOT.joinpath(*parts)


def create_gemini_engine(model: str = "gemini-2.5-flash"):
    """创建使用 Gemini 的手工测试翻译引擎。"""
    from translation_engine import APIConfig, APIProvider, TranslationEngine

    engine = TranslationEngine()
    engine.add_api_config(
        "gemini",
        APIConfig(
            provider=APIProvider.GEMINI,
            api_key=require_env("GEMINI_API_KEY"),
            model=model,
        ),
    )
    return engine
