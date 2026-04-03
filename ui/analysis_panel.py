#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext


class AnalysisPanel:
    """解析面板，仅负责布局和控件暴露。"""

    def __init__(
        self,
        notebook,
        analysis_status_var,
        on_analysis_segment_select,
        on_analyze_selected_segment,
        on_copy_analysis_content,
    ):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="解析")

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(1, weight=1)

        ttk.Label(
            self.frame,
            text="对翻译段落进行解析讲解（情节解读、概念解释等）",
            foreground="gray",
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))

        analysis_list_frame = ttk.Frame(self.frame)
        analysis_list_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W), padx=(0, 10))

        ttk.Label(analysis_list_frame, text="段落列表").pack(anchor=tk.W)
        self.analysis_listbox = tk.Listbox(analysis_list_frame, width=30, height=12)
        self.analysis_listbox.pack(fill=tk.Y, expand=True)
        self.analysis_listbox.bind("<<ListboxSelect>>", on_analysis_segment_select)

        analysis_detail_frame = ttk.Frame(self.frame)
        analysis_detail_frame.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        analysis_detail_frame.columnconfigure(0, weight=1)
        analysis_detail_frame.rowconfigure(1, weight=1)

        ttk.Label(analysis_detail_frame, text="解析内容").grid(row=0, column=0, sticky=tk.W)
        self.analysis_text = scrolledtext.ScrolledText(analysis_detail_frame, wrap=tk.WORD, height=12)
        self.analysis_text.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        analysis_btn_frame = ttk.Frame(self.frame)
        analysis_btn_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        ttk.Button(
            analysis_btn_frame,
            text="解析选中段落",
            command=on_analyze_selected_segment,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            analysis_btn_frame,
            text="复制解析",
            command=on_copy_analysis_content,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(self.frame, textvariable=analysis_status_var, foreground="gray").grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0)
        )
