#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""失败段落 feature 聚合层。"""


class FailedSegmentFeature:
    """Aggregate failed-segment UI, state selection, and actions."""

    def __init__(self, gui):
        self.gui = gui
        self.panel = None
        self.controller = None
        self.actions = None

    def attach_panel(self, panel):
        self.panel = panel
        if self.controller is not None:
            self.controller.bind_panel(panel)

    def attach_controller(self, controller):
        self.controller = controller
        if self.panel is not None:
            self.controller.bind_panel(self.panel)

    def attach_actions(self, actions):
        self.actions = actions

    def refresh(self):
        if self.controller is not None:
            self.controller.refresh()
            return
        if self.panel is not None:
            self.gui.selected_failed_index = None
            self.panel.populate_failed_segments(self.gui.failed_segments)

    def handle_selection(self):
        if self.controller is not None:
            return self.controller.handle_selection()
        return None

    def get_selected_segment(self):
        if self.controller is not None:
            return self.controller.get_selected_segment()

        idx = self.gui.selected_failed_index
        if idx is None or not self.gui.failed_segments:
            return None
        if idx < 0 or idx >= len(self.gui.failed_segments):
            self.gui.selected_failed_index = None
            return None
        return self.gui.failed_segments[idx]

    def get_manual_translation(self):
        if self.controller is not None:
            return self.controller.get_manual_translation()
        if self.panel is not None:
            return self.panel.get_manual_translation()
        return ""

    def retry_selected(self):
        if self.actions is None:
            raise RuntimeError("FailedSegmentActions 尚未装配")
        return self.actions.retry_selected()

    def save_manual_translation(self):
        if self.actions is None:
            raise RuntimeError("FailedSegmentActions 尚未装配")
        return self.actions.save_manual_translation()

    def update_retry_api_names(self, api_names):
        if self.panel is not None:
            self.panel.set_retry_api_names(api_names)

    def bind_all(self, panel=None, controller=None, actions=None):
        if actions is not None:
            self.attach_actions(actions)
        if controller is not None:
            self.attach_controller(controller)
        if panel is not None:
            self.attach_panel(panel)
