"""Failed segment state helpers.

Keep retry/manual-fix bookkeeping out of the Tk GUI class.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional


class FailedSegmentManager:
    def __init__(self) -> None:
        self._items: List[Dict] = []
        self._selected_index: Optional[int] = None

    def reset(self) -> None:
        self._items = []
        self._selected_index = None

    def replace_all(self, items: List[Dict]) -> None:
        self._items = [self._normalize_item(item) for item in items or []]
        self._selected_index = None

    def append(self, **kwargs) -> Dict:
        item = self._normalize_item(kwargs)
        self._items.append(item)
        return item

    def get_all(self) -> List[Dict]:
        return deepcopy(self._items)

    def select_by_list_index(self, index: int) -> Optional[Dict]:
        if index < 0 or index >= len(self._items):
            self._selected_index = None
            return None
        self._selected_index = index
        return deepcopy(self._items[index])

    def get_selected(self) -> Optional[Dict]:
        if self._selected_index is None:
            return None
        if self._selected_index >= len(self._items):
            return None
        return deepcopy(self._items[self._selected_index])

    def update_selected_translation(self, translated_text: str) -> bool:
        if self._selected_index is None or self._selected_index >= len(self._items):
            return False
        self._items[self._selected_index]['translated_text'] = (translated_text or '').strip()
        return True

    def sync_translated_segments(self, translated_segments: List[str]) -> None:
        for item in self._items:
            idx = item.get('segment_index')
            if isinstance(idx, int) and 0 <= idx < len(translated_segments):
                item['translated_text'] = translated_segments[idx]

    def build_display_label(self, item: Dict) -> str:
        index = item.get('segment_index', '?')
        error = (item.get('error') or '').strip()
        if error:
            return f"段落 {index + 1}: {error[:50]}"
        return f"段落 {index + 1}: 待重试"

    def build_status_text(self, selected: Optional[Dict] = None) -> str:
        total = len(self._items)
        if total == 0:
            return '暂无失败段落'
        if not selected:
            return f'共有 {total} 个失败段落，可逐个重试或手动修正'
        idx = selected.get('segment_index', 0)
        err = (selected.get('error') or '').strip()
        return f'当前选择：第 {idx + 1} 段' + (f'；错误：{err}' if err else '')

    def build_retry_request(self, retry_api_name: str, target_language: str) -> Optional[Dict]:
        selected = self.get_selected()
        if not selected:
            return None
        return {
            'segment_index': selected.get('segment_index'),
            'source_text': selected.get('source_text', ''),
            'existing_translation': selected.get('translated_text', ''),
            'retry_api_name': retry_api_name,
            'target_language': target_language,
        }

    def _normalize_item(self, item: Optional[Dict]) -> Dict:
        item = dict(item or {})
        return {
            'segment_index': item.get('segment_index', -1),
            'source_text': item.get('source_text', ''),
            'translated_text': item.get('translated_text', ''),
            'error': item.get('error', ''),
            'api_name': item.get('api_name', ''),
            'model_name': item.get('model_name', ''),
        }
