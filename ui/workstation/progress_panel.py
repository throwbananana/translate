#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk


class ProgressPanel:
    """进度条与状态文本区域。"""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        self.progress_text_var = tk.StringVar(value="就绪")
        ttk.Label(self.frame, textvariable=self.progress_text_var).grid(row=1, column=0, sticky=tk.W)
