#! python
# -*- coding: utf-8 -*-
"""运行时状态持久化工具。

把批量任务队列和翻译进度缓存从 GUI 主类中抽离出来，
统一管理用户级运行时文件，并兼容旧版仓库目录下的文件迁移。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from app_paths import get_runtime_file


class RuntimeStateStore:
    """负责读写批量任务和翻译进度等运行时状态。"""

    def __init__(
        self,
        progress_cache_path: Optional[Path] = None,
        batch_queue_path: Optional[Path] = None,
        legacy_root: Optional[Path] = None,
    ) -> None:
        self.progress_cache_path = Path(progress_cache_path) if progress_cache_path else get_runtime_file('translation_cache.json')
        self.batch_queue_path = Path(batch_queue_path) if batch_queue_path else get_runtime_file('batch_tasks.json')
        self.legacy_root = Path(legacy_root) if legacy_root else Path(__file__).resolve().parent

        self._migrate_legacy_file('translation_cache.json', self.progress_cache_path)
        self._migrate_legacy_file('batch_tasks.json', self.batch_queue_path)

    def _migrate_legacy_file(self, legacy_name: str, target_path: Path) -> None:
        legacy_path = self.legacy_root / legacy_name
        if target_path.exists() or not legacy_path.exists() or legacy_path.resolve() == target_path.resolve():
            return

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legacy_path, target_path)
            print(f"ℹ️ 已迁移运行时文件到用户目录: {target_path}")
        except Exception as e:
            print(f"⚠️ 迁移运行时文件失败 ({legacy_name}): {e}")

    def load_batch_queue(self) -> List[Dict[str, Any]]:
        return self._read_json(self.batch_queue_path, default=[])

    def save_batch_queue(self, batch_queue: List[Dict[str, Any]]) -> None:
        self._write_json(self.batch_queue_path, batch_queue, indent=2)

    def load_progress(self) -> Optional[Dict[str, Any]]:
        return self._read_json(self.progress_cache_path, default=None)

    def save_progress(self, data: Dict[str, Any]) -> None:
        self._write_json(self.progress_cache_path, data)

    def clear_progress(self) -> None:
        if self.progress_cache_path.exists():
            self.progress_cache_path.unlink()

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_json(self, path: Path, data: Any, indent: Optional[int] = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
