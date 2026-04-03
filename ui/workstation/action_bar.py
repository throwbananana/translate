#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk


class ActionBar:
    """工作台操作按钮区。"""

    def __init__(
        self,
        parent,
        on_start_translation,
        on_stop_translation,
        on_start_batch_analysis,
        on_stop_analysis,
        on_export_translation,
        on_export_bilingual_epub,
        on_export_audiobook,
        on_export_analysis,
        on_clear_all,
    ):
        self.frame = ttk.Frame(parent)
        self.frame.grid(row=4, column=0, sticky=(tk.W, tk.E))

        self.translate_btn = ttk.Button(
            self.frame,
            text="开始翻译",
            command=on_start_translation,
        )
        self.translate_btn.grid(row=0, column=0, padx=5, pady=2)

        self.stop_btn = ttk.Button(
            self.frame,
            text="停止",
            command=on_stop_translation,
            state="disabled",
        )
        self.stop_btn.grid(row=0, column=1, padx=5, pady=2)

        self.analyze_all_btn = ttk.Button(
            self.frame,
            text="一键解析全部",
            command=on_start_batch_analysis,
        )
        self.analyze_all_btn.grid(row=0, column=2, padx=5, pady=2)

        self.stop_analysis_btn = ttk.Button(
            self.frame,
            text="停止解析",
            command=on_stop_analysis,
            state="disabled",
        )
        self.stop_analysis_btn.grid(row=0, column=3, padx=5, pady=2)

        ttk.Button(self.frame, text="导出译文", command=on_export_translation).grid(
            row=0,
            column=4,
            padx=5,
            pady=2,
        )
        ttk.Button(self.frame, text="导出双语书", command=on_export_bilingual_epub).grid(
            row=0,
            column=5,
            padx=5,
            pady=2,
        )
        ttk.Button(self.frame, text="导出有声书", command=on_export_audiobook).grid(
            row=0,
            column=6,
            padx=5,
            pady=2,
        )
        ttk.Button(self.frame, text="导出解析", command=on_export_analysis).grid(
            row=0,
            column=7,
            padx=5,
            pady=2,
        )
        ttk.Button(self.frame, text="清空", command=on_clear_all).grid(
            row=0,
            column=8,
            padx=5,
            pady=2,
        )
