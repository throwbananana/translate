#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext


class FailedSegmentsPanel:
    """失败段落面板，仅负责布局和控件暴露。"""

    def __init__(
        self,
        notebook,
        api_names,
        retry_api_var,
        failed_status_var,
        on_failed_select,
        on_open_retry_config,
        on_retry_translation,
        on_save_manual_translation,
    ):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="失败段落")

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(3, weight=1)

        ttk.Label(
            self.frame,
            text="检测到的失败/未完成段落，可重试或手动翻译后替换。",
            foreground="gray",
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))

        self.failed_listbox = tk.Listbox(self.frame, height=8)
        self.failed_listbox.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W), padx=(0, 10))
        self.failed_listbox.bind("<<ListboxSelect>>", on_failed_select)

        detail_frame = ttk.Frame(self.frame)
        detail_frame.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(1, weight=1)
        detail_frame.rowconfigure(3, weight=1)

        ttk.Label(detail_frame, text="原文（只读）").grid(row=0, column=0, sticky=tk.W)
        self.failed_source_text = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, height=6, state="disabled"
        )
        self.failed_source_text.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(0, 5))

        ttk.Label(detail_frame, text="手动翻译").grid(row=2, column=0, sticky=tk.W)
        self.manual_translation_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, height=6)
        self.manual_translation_text.grid(row=3, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        retry_api_frame = ttk.Frame(detail_frame)
        retry_api_frame.grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(retry_api_frame, text="重试API:").pack(side=tk.LEFT)
        self.retry_api_combo = ttk.Combobox(
            retry_api_frame,
            textvariable=retry_api_var,
            values=api_names,
            state="readonly",
            width=22,
        )
        self.retry_api_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(retry_api_frame, text="配置", command=on_open_retry_config).pack(side=tk.LEFT)

        button_frame = ttk.Frame(detail_frame)
        button_frame.grid(row=5, column=0, sticky=tk.E, pady=(5, 0))
        ttk.Button(button_frame, text="重试翻译", command=on_retry_translation).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="保存手动翻译", command=on_save_manual_translation).grid(
            row=0, column=1, padx=5
        )

        ttk.Label(self.frame, textvariable=failed_status_var).grid(
            row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0)
        )
