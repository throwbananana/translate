#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""失败段落 controller：连接列表选择、详情展示与手动译文读取。"""


class FailedSegmentController:
    """Coordinate failed-segment panel state with GUI runtime state."""

    def __init__(self, gui, panel):
        self.gui = gui
        self.panel = panel

    def refresh(self):
        if self.panel is None:
            return
        self.gui.selected_failed_index = None
        self.panel.populate_failed_segments(self.gui.failed_segments)

    def handle_selection(self):
        if self.panel is None or not self.gui.failed_segments:
            self.gui.selected_failed_index = None
            return None

        idx = self.panel.get_selected_index()
        if idx is None or idx >= len(self.gui.failed_segments):
            self.gui.selected_failed_index = None
            return None

        self.gui.selected_failed_index = idx
        info = self.gui.failed_segments[idx]
        self.panel.show_failed_source(info['source'])
        return info

    def get_selected_segment(self):
        idx = self.gui.selected_failed_index
        if idx is None or not self.gui.failed_segments:
            return None
        if idx < 0 or idx >= len(self.gui.failed_segments):
            self.gui.selected_failed_index = None
            return None
        return self.gui.failed_segments[idx]

    def get_manual_translation(self):
        if self.panel is None:
            return ""
        return self.panel.get_manual_translation()

    def bind_panel(self, panel):
        self.panel = panel
