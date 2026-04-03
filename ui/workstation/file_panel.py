#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk


class FilePanel:
    """文件选择与文件信息区域。"""

    def __init__(
        self,
        parent,
        support_formats_text,
        on_browse_file,
        on_open_batch_window,
        on_open_glossary_editor,
        on_toggle_preview,
    ):
        self.frame = ttk.LabelFrame(parent, text="文件选择", padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.frame.columnconfigure(1, weight=1)

        ttk.Label(self.frame, text="选择文件:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.file_path_var, state="readonly").grid(
            row=0,
            column=1,
            sticky=(tk.W, tk.E),
            padx=5,
        )
        ttk.Button(self.frame, text="浏览...", command=on_browse_file).grid(row=0, column=2, padx=5)
        ttk.Button(self.frame, text="批量任务...", command=on_open_batch_window).grid(row=0, column=3, padx=5)
        ttk.Button(self.frame, text="术语表管理", command=on_open_glossary_editor).grid(row=0, column=4, padx=5)

        ttk.Label(self.frame, text=support_formats_text, foreground="gray").grid(
            row=1,
            column=0,
            columnspan=3,
            sticky=tk.W,
            pady=(5, 0),
        )

        preview_frame = ttk.Frame(self.frame)
        preview_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))

        self.file_info_var = tk.StringVar(value="")
        ttk.Label(preview_frame, textvariable=self.file_info_var, foreground="blue").pack(side=tk.LEFT)

        self.cost_var = tk.StringVar(value="")
        ttk.Label(preview_frame, textvariable=self.cost_var, foreground="green").pack(side=tk.LEFT, padx=(10, 0))

        self.toggle_preview_btn = ttk.Button(
            preview_frame,
            text="显示完整原文",
            command=on_toggle_preview,
            state="disabled",
        )
        self.toggle_preview_btn.pack(side=tk.RIGHT, padx=5)
