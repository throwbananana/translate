import textwrap

import pytest

from tools.wire_gui_translation_session import apply_wiring_patch


pytestmark = pytest.mark.unit


BASE_GUI_SNIPPET = textwrap.dedent(
    '''\
    from ui.workstation import ActionBar, ApiPanel, FilePanel, ProgressPanel

    class BookTranslatorGUI:
        def __init__(self, root):
            self.translation_thread = None
            self.source_segments = []

        def stop_translation(self):
            """停止翻译"""
            self.is_translating = False
            self.translate_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.progress_text_var.set("翻译已停止")
    '''
)


def test_apply_wiring_patch_adds_import_state_and_stop_cancellation():
    patched = apply_wiring_patch(BASE_GUI_SNIPPET)

    assert "from controllers import (" in patched
    assert "TranslationRunGuard" in patched
    assert "cancel_gui_translation_session" in patched
    assert "self.translation_run_guard = TranslationRunGuard()" in patched
    assert "self.current_translation_session = None" in patched
    assert "cancel_gui_translation_session(self.translation_run_guard)" in patched
    assert "self.current_translation_session = None" in patched


def test_apply_wiring_patch_is_idempotent():
    once = apply_wiring_patch(BASE_GUI_SNIPPET)
    twice = apply_wiring_patch(once)

    assert twice == once
    assert twice.count("from controllers import (") == 1
    assert twice.count("self.translation_run_guard = TranslationRunGuard()") == 1
    assert twice.count("cancel_gui_translation_session(self.translation_run_guard)") == 1


def test_apply_wiring_patch_fails_when_expected_anchor_is_missing():
    with pytest.raises(ValueError):
        apply_wiring_patch("class BookTranslatorGUI:\n    pass\n")
