#! python
# -*- coding: utf-8 -*-
"""Patch `book_translator_gui.pyw` toward guarded translation sessions.

The GitHub contents API replaces whole files, while `book_translator_gui.pyw` is a
large legacy GUI module.  This tool keeps the first GUI wiring step reproducible
and reviewable by applying small, idempotent text transformations locally.

Current scope is intentionally conservative:

1. import the controller session/workflow helpers;
2. initialize `TranslationRunGuard` and `current_translation_session` in the GUI;
3. make `stop_translation()` cancel the active guarded session.

The next migration pass can extend this tool to rewrite `start_translation()`,
`translate_text()` and `translate_segment()` after the first guarded-session
plumbing is verified in the actual GUI file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TARGET = Path("book_translator_gui.pyw")

IMPORT_ANCHOR = "from ui.workstation import ActionBar, ApiPanel, FilePanel, ProgressPanel\n"
CONTROLLER_IMPORT = """from controllers import (
    TranslationRunGuard,
    cancel_gui_translation_session,
)
"""

INIT_ANCHOR = "        self.translation_thread = None\n"
INIT_GUARD_STATE = """        self.translation_run_guard = TranslationRunGuard()
        self.current_translation_session = None
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


def apply_wiring_patch(text: str) -> str:
    """Return `book_translator_gui.pyw` with first-pass session wiring applied."""
    text = _insert_after_once(text, IMPORT_ANCHOR, CONTROLLER_IMPORT)
    text = _insert_after_once(text, INIT_ANCHOR, INIT_GUARD_STATE)
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
        print(f"{path} is already wired for the first guarded session pass")
        return 0

    if patched == original:
        print(f"{path} already up to date")
        return 0

    path.write_text(patched, encoding="utf-8")
    print(f"Applied guarded session wiring to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
