#! python
# -*- coding: utf-8 -*-
"""Patch `book_translator_gui.pyw` toward guarded translation sessions.

The GitHub contents API replaces whole files, while `book_translator_gui.pyw` is a
large legacy GUI module.  This tool keeps GUI wiring steps reproducible and
reviewable by applying small, idempotent text transformations locally.

Current scope is conservative but now covers the first start/stop migration pass:

1. import the controller session/workflow helpers;
2. initialize `TranslationRunGuard` and `current_translation_session` in the GUI;
3. move `start_translation()` resume/reset planning into `start_gui_translation_session(...)`;
4. pass the created session to the translation worker thread;
5. make `stop_translation()` cancel the active guarded session.

The next migration pass can extend this tool to rewrite `translate_text()` and
`translate_segment()` after the first guarded-session plumbing is verified in the
actual GUI file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TARGET = Path("book_translator_gui.pyw")

IMPORT_ANCHOR = "from ui.workstation import ActionBar, ApiPanel, FilePanel, ProgressPanel\n"
CONTROLLER_IMPORT = """from controllers import (
    TranslationRunGuard,
    cancel_gui_translation_session,
    start_gui_translation_session,
)
"""
LEGACY_CONTROLLER_IMPORT = """from controllers import (
    TranslationRunGuard,
    cancel_gui_translation_session,
)
"""

INIT_ANCHOR = "        self.translation_thread = None\n"
INIT_GUARD_STATE = """        self.translation_run_guard = TranslationRunGuard()
        self.current_translation_session = None
"""

START_LEGACY_SESSION_PLAN = """        # 计算签名用于断点恢复判断
        current_signature = self.compute_text_signature(self.current_text)
        resume_possible = (
            self.text_signature == current_signature
            and self.source_segments
            and 0 < len(self.translated_segments) < len(self.source_segments)
        )

        # 是否从断点继续
        self.resume_from_index = 0
        if resume_possible:
            resume = messagebox.askyesno(
                "继续翻译",
                f"检测到上次未完成的翻译，是否从第 {len(self.translated_segments) + 1} 段继续？"
            )
            if resume:
                self.resume_from_index = len(self.translated_segments)
                # 确保译文长度与起始段对齐
                if len(self.translated_segments) > self.resume_from_index:
                    self.translated_segments = self.translated_segments[:self.resume_from_index]
            else:
                self.translated_segments = []
                self.source_segments = []
                self.failed_segments = []
        else:
            self.translated_segments = []
            self.source_segments = []
            self.failed_segments = []
"""

START_SESSION_PLAN = """        # 计算签名用于断点恢复判断，并通过 controller 生成本次会话快照
        current_signature = self.compute_text_signature(self.current_text)
        resume_possible = (
            self.text_signature == current_signature
            and self.source_segments
            and 0 < len(self.translated_segments) < len(self.source_segments)
        )
        resume_requested = False
        if resume_possible:
            resume_requested = messagebox.askyesno(
                "继续翻译",
                f"检测到上次未完成的翻译，是否从第 {len(self.translated_segments) + 1} 段继续？"
            )

        session = start_gui_translation_session(
            self.translation_run_guard,
            api_type=api_type,
            target_language=self.target_language_var,
            style=self.style_var,
            concurrency=self.concurrency_var,
            current_signature=current_signature,
            cached_signature=self.text_signature,
            source_segments=self.source_segments,
            translated_segments=self.translated_segments,
            failed_segments=self.failed_segments,
            resume_requested=resume_requested,
        )
        self.current_translation_session = session
        start_state = session.start_state
        self.resume_from_index = start_state.resume_from_index
        self.source_segments = list(start_state.source_segments)
        self.translated_segments = list(start_state.translated_segments)
        self.failed_segments = list(start_state.failed_segments)
"""

START_LEGACY_PROGRESS = """        self.progress_var.set(
            (self.resume_from_index / max(len(self.source_segments), 1)) * 100
            if self.resume_from_index and self.source_segments else 0
        )
        if not self.resume_from_index:
            self.translated_text = ""
            self.translated_text_widget.delete('1.0', tk.END)
        self.failed_segments = []
"""

START_SESSION_PROGRESS = """        self.progress_var.set(start_state.initial_progress)
        if start_state.should_clear_translated_text:
            self.translated_text = ""
            self.translated_text_widget.delete('1.0', tk.END)
"""

THREAD_OLD = """        # 在新线程中执行翻译
        self.translation_thread = threading.Thread(target=self.translate_text, daemon=True)
        self.translation_thread.start()
"""

THREAD_NEW = """        # 在新线程中执行翻译
        self.translation_thread = threading.Thread(
            target=self.translate_text,
            args=(session,),
            daemon=True,
        )
        self.translation_thread.start()
"""

STOP_OLD = """    def stop_translation(self):
        \"\"\"停止翻译\"\"\"
        self.is_translating = False
        self.translate_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_text_var.set(\"翻译已停止\")
"""

STOP_NEW = """    def stop_translation(self):
        \"\"\"停止翻译\"\"\"
        cancel_gui_translation_session(self.translation_run_guard)
        self.current_translation_session = None
        self.is_translating = False
        self.translate_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_text_var.set(\"翻译已停止\")
"""


def _insert_after_once(text: str, anchor: str, insertion: str) -> str:
    if insertion in text:
        return text
    if anchor not in text:
        raise ValueError(f"Anchor not found: {anchor!r}")
    return text.replace(anchor, anchor + insertion, 1)


def _replace_once(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise ValueError("Expected source block was not found")
    return text.replace(old, new, 1)


def _ensure_controller_import(text: str) -> str:
    if CONTROLLER_IMPORT in text:
        return text
    if LEGACY_CONTROLLER_IMPORT in text:
        return text.replace(LEGACY_CONTROLLER_IMPORT, CONTROLLER_IMPORT, 1)
    return _insert_after_once(text, IMPORT_ANCHOR, CONTROLLER_IMPORT)


def apply_wiring_patch(text: str) -> str:
    """Return `book_translator_gui.pyw` with guarded session wiring applied."""
    text = _ensure_controller_import(text)
    text = _insert_after_once(text, INIT_ANCHOR, INIT_GUARD_STATE)
    text = _replace_once(text, START_LEGACY_SESSION_PLAN, START_SESSION_PLAN)
    text = _replace_once(text, START_LEGACY_PROGRESS, START_SESSION_PROGRESS)
    text = _replace_once(text, THREAD_OLD, THREAD_NEW)
    text = _replace_once(text, STOP_OLD, STOP_NEW)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default=TARGET,
        type=Path,
        help="Path to book_translator_gui.pyw",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the file would change instead of writing it.",
    )
    args = parser.parse_args()

    path = args.path
    original = path.read_text(encoding="utf-8")
    patched = apply_wiring_patch(original)

    if args.check:
        if patched != original:
            print(f"{path} needs guarded session wiring")
            return 1
        print(f"{path} is already wired for the guarded session pass")
        return 0

    if patched == original:
        print(f"{path} already up to date")
        return 0

    path.write_text(patched, encoding="utf-8")
    print(f"Applied guarded session wiring to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
