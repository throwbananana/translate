from tkinter import messagebox

from retry_failed_segment_service import RetryActionStatus


class FailedSegmentActions:
    """Encapsulate failed-segment retry and manual replacement flows."""

    def __init__(self, gui):
        self.gui = gui

    def retry_selected(self):
        info = self._get_selected_segment(require_message="请先选择需要重试的段落")
        if info is None:
            return

        api_type = self.gui.ensure_retry_api_ready() if hasattr(self.gui, 'ensure_retry_api_ready') else self.gui.get_retry_api_type()
        if not api_type:
            return

        service = self._get_service()
        if service is None:
            messagebox.showerror("错误", "失败段重试服务未初始化")
            return

        result = service.retry_failed_segment(
            selected_failed_index=self.gui.selected_failed_index,
            failed_segments=self.gui.failed_segments,
            translated_segments=self.gui.translated_segments,
            api_type=api_type,
            api_configs=self.gui.api_configs,
            custom_local_models=self.gui.custom_local_models,
            openai_support=self._has_openai_support(),
            translate_segment=self.gui.translate_segment,
            is_translation_incomplete=self.gui.is_translation_incomplete,
            target_language=self.gui.get_target_language(),
        )

        if result.status == RetryActionStatus.CONFIG_LOCAL_MODEL:
            messagebox.showwarning("警告", result.message)
            self.gui.open_edit_local_model_dialog(api_type)
            return
        if result.status == RetryActionStatus.CONFIG_API:
            messagebox.showwarning("警告", result.message)
            self.gui.open_api_config(api_type)
            return
        if result.status == RetryActionStatus.UNSUPPORTED:
            messagebox.showerror("错误", result.message)
            return
        if result.status == RetryActionStatus.FAILED:
            messagebox.showerror("错误", result.message)
            return
        if result.status == RetryActionStatus.INCOMPLETE:
            messagebox.showwarning("提示", result.message)
            return
        if result.status != RetryActionStatus.SUCCESS:
            return

        self.gui.rebuild_translated_text()
        self.gui.refresh_failed_segments_view()
        self.gui.save_progress_cache()
        messagebox.showinfo("成功", result.message)

    def save_manual_translation(self):
        info = self._get_selected_segment(require_message="请先选择需要替换的段落")
        if info is None:
            return

        manual_text = self._get_manual_translation()
        service = self._get_service()
        if service is None:
            messagebox.showerror("错误", "失败段修正服务未初始化")
            return

        result = service.save_manual_translation(
            selected_failed_index=self.gui.selected_failed_index,
            failed_segments=self.gui.failed_segments,
            translated_segments=self.gui.translated_segments,
            manual_text=manual_text,
            translation_memory=self.gui.translation_memory,
            target_language=self.gui.get_target_language(),
        )

        if result.status == RetryActionStatus.EMPTY_TRANSLATION:
            messagebox.showwarning("警告", result.message)
            return
        if result.status == RetryActionStatus.SELECT_REQUIRED:
            messagebox.showinfo("提示", result.message)
            return
        if result.status != RetryActionStatus.SUCCESS:
            messagebox.showerror("错误", result.message)
            return

        self.gui.rebuild_translated_text()
        self.gui.refresh_failed_segments_view()
        self.gui.save_progress_cache()
        messagebox.showinfo("成功", result.message)

    def _get_selected_segment(self, require_message):
        info = None
        if hasattr(self.gui, 'get_selected_failed_segment'):
            info = self.gui.get_selected_failed_segment()
        elif self.gui.selected_failed_index is not None and self.gui.failed_segments:
            info = self.gui.failed_segments[self.gui.selected_failed_index]

        if info is None:
            messagebox.showinfo("提示", require_message)
            return None
        return info

    def _get_manual_translation(self):
        if hasattr(self.gui, 'failed_segment_feature'):
            return self.gui.failed_segment_feature.get_manual_translation()
        if hasattr(self.gui, 'failed_segment_controller'):
            return self.gui.failed_segment_controller.get_manual_translation()
        if hasattr(self.gui, 'failed_panel'):
            return self.gui.failed_panel.get_manual_translation()
        return self.gui.manual_translation_text.get('1.0', 'end').strip()

    def _get_service(self):
        return getattr(self.gui, 'retry_failed_segment_service', None)

    @staticmethod
    def _has_openai_support():
        try:
            import openai  # noqa: F401
            return True
        except Exception:
            return False
