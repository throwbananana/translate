import textwrap

import pytest

from tools.wire_gui_translation_session import (
    TRANSLATE_SEGMENT_LEGACY,
    TRANSLATE_TEXT_LEGACY,
    apply_wiring_patch,
)


pytestmark = pytest.mark.unit


BASE_GUI_SNIPPET = textwrap.dedent(
    '''\
    from ui.workstation import ActionBar, ApiPanel, FilePanel, ProgressPanel

    class BookTranslatorGUI:
        def __init__(self, root):
            self.translation_thread = None
            self.source_segments = []

        def start_translation(self):
            """开始翻译"""
            if not self.current_text:
                messagebox.showwarning("警告", "请先加载要翻译的文件")
                return

            api_type = self.get_translation_api_type()
            if not self._ensure_provider_ready_or_prompt(api_type):
                return

            # 计算签名用于断点恢复判断
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

            # 开始翻译
            self.lm_studio_fallback_active = False
            self.consecutive_failures = 0
            self.paused_due_to_failures = False
            self.is_translating = True
            self.translate_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.progress_var.set(
                (self.resume_from_index / max(len(self.source_segments), 1)) * 100
                if self.resume_from_index and self.source_segments else 0
            )
            if not self.resume_from_index:
                self.translated_text = ""
                self.translated_text_widget.delete('1.0', tk.END)
            self.failed_segments = []
            self.selected_failed_index = None
            self.refresh_failed_segments_view()

            # 在新线程中执行翻译
            self.translation_thread = threading.Thread(target=self.translate_text, daemon=True)
            self.translation_thread.start()

        def stop_translation(self):
            """停止翻译"""
            self.is_translating = False
            self.translate_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.progress_text_var.set("翻译已停止")
    '''
)

BASE_GUI_SNIPPET += "\n" + TRANSLATE_TEXT_LEGACY + "\n" + TRANSLATE_SEGMENT_LEGACY


def test_apply_wiring_patch_adds_import_state_session_start_and_stop_cancellation():
    patched = apply_wiring_patch(BASE_GUI_SNIPPET)

    assert "from controllers import (" in patched
    assert "GuiTranslationWorkerCallbacks" in patched
    assert "TranslationRunGuard" in patched
    assert "cancel_gui_translation_session" in patched
    assert "run_guarded_gui_translation_lifecycle" in patched
    assert "schedule_gui_translation_final_state" in patched
    assert "start_gui_translation_session" in patched
    assert "self.translation_run_guard = TranslationRunGuard()" in patched
    assert "self.current_translation_session = None" in patched
    assert "session = start_gui_translation_session(" in patched
    assert "self.current_translation_session = session" in patched
    assert "start_state = session.start_state" in patched
    assert "self.progress_var.set(start_state.initial_progress)" in patched
    assert "args=(session,)" in patched
    assert "cancel_gui_translation_session(self.translation_run_guard)" in patched


def test_apply_wiring_patch_rewrites_worker_lifecycle_and_segment_config_snapshot():
    patched = apply_wiring_patch(BASE_GUI_SNIPPET)

    assert "def translate_text(self, session=None):" in patched
    assert "callbacks = GuiTranslationWorkerCallbacks(" in patched
    assert "run_guarded_gui_translation_lifecycle(" in patched
    assert "schedule_gui_translation_final_state(" in patched
    assert "def _apply_guarded_translation_finish_state(self, finish_state):" in patched
    assert "def translate_segment(self, api_type, text, context=None, config=None):" in patched
    assert "target_language = config.target_language if config is not None else self.get_target_language()" in patched
    assert "style_guide = config.style_prompt" in patched
    assert "self.concurrency_var.get()" not in patched


def test_apply_wiring_patch_removes_legacy_start_translation_blocks():
    patched = apply_wiring_patch(BASE_GUI_SNIPPET)

    assert "# 是否从断点继续" not in patched
    assert "resume = messagebox.askyesno" not in patched
    assert "self.failed_segments = []\n            self.selected_failed_index" not in patched
    assert "threading.Thread(target=self.translate_text, daemon=True)" not in patched


def test_apply_wiring_patch_upgrades_legacy_controller_import():
    legacy_imported = BASE_GUI_SNIPPET.replace(
        "from ui.workstation import ActionBar, ApiPanel, FilePanel, ProgressPanel\n",
        "from ui.workstation import ActionBar, ApiPanel, FilePanel, ProgressPanel\n"
        "from controllers import (\n"
        "    TranslationRunGuard,\n"
        "    cancel_gui_translation_session,\n"
        ")\n",
    )

    patched = apply_wiring_patch(legacy_imported)

    assert "GuiTranslationWorkerCallbacks" in patched
    assert "run_guarded_gui_translation_lifecycle" in patched
    assert patched.count("from controllers import (") == 1


def test_apply_wiring_patch_is_idempotent():
    once = apply_wiring_patch(BASE_GUI_SNIPPET)
    twice = apply_wiring_patch(once)

    assert twice == once
    assert twice.count("from controllers import (") == 1
    assert twice.count("self.translation_run_guard = TranslationRunGuard()") == 1
    assert twice.count("session = start_gui_translation_session(") == 1
    assert twice.count("run_guarded_gui_translation_lifecycle(") == 1
    assert twice.count("def translate_segment(self, api_type, text, context=None, config=None):") == 1
    assert twice.count("cancel_gui_translation_session(self.translation_run_guard)") == 1


def test_apply_wiring_patch_fails_when_expected_anchor_is_missing():
    with pytest.raises(ValueError):
        apply_wiring_patch("class BookTranslatorGUI:\n    pass\n")
