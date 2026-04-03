#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext


class ContentNotebook:
    """原文/译文/双栏对照内容区。"""

    def __init__(
        self,
        paned_parent,
        sync_scroll_var,
        on_save_comparison_edits,
        on_source_scroll,
        on_target_scroll,
        on_mousewheel,
    ):
        self.notebook = ttk.Notebook(paned_parent)
        paned_parent.add(self.notebook, minsize=500)

        self.sync_scroll_var = sync_scroll_var

        original_frame = ttk.Frame(self.notebook)
        self.notebook.add(original_frame, text="原文")
        original_frame.columnconfigure(0, weight=1)
        original_frame.rowconfigure(0, weight=1)
        self.original_text = scrolledtext.ScrolledText(original_frame, wrap=tk.WORD, height=15)
        self.original_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        translated_frame = ttk.Frame(self.notebook)
        self.notebook.add(translated_frame, text="译文")
        translated_frame.columnconfigure(0, weight=1)
        translated_frame.rowconfigure(0, weight=1)
        self.translated_text_widget = scrolledtext.ScrolledText(
            translated_frame,
            wrap=tk.WORD,
            height=15,
        )
        self.translated_text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        comparison_frame = ttk.Frame(self.notebook)
        self.notebook.add(comparison_frame, text="双栏对照")

        toolbar = ttk.Frame(comparison_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        ttk.Checkbutton(toolbar, text="同步滚动", variable=self.sync_scroll_var).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="保存右侧修改", command=on_save_comparison_edits).pack(side=tk.LEFT, padx=10)

        paned = tk.PanedWindow(comparison_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.LabelFrame(paned, text="原文")
        paned.add(left_frame, minsize=100)
        self.comp_source_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=15)
        self.comp_source_text.pack(fill=tk.BOTH, expand=True)
        self.comp_source_text.config(state="disabled")

        right_frame = ttk.LabelFrame(paned, text="译文 (可编辑)")
        paned.add(right_frame, minsize=100)
        self.comp_target_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=15)
        self.comp_target_text.pack(fill=tk.BOTH, expand=True)

        self.comp_source_text.vbar.config(command=on_source_scroll)
        self.comp_target_text.vbar.config(command=on_target_scroll)
        self.comp_source_text.bind("<MouseWheel>", lambda event: on_mousewheel(event, self.comp_target_text))
        self.comp_target_text.bind("<MouseWheel>", lambda event: on_mousewheel(event, self.comp_source_text))
