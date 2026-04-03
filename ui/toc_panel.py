#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk


class TocPanel:
    """章节目录侧边栏。"""

    def __init__(self, paned_parent, on_toc_click):
        self.frame = ttk.Frame(paned_parent, width=200)
        paned_parent.add(self.frame, minsize=150)

        ttk.Label(self.frame, text="章节目录 (自动识别)").pack(anchor=tk.W, padx=5, pady=5)
        self.toc_tree = ttk.Treeview(self.frame, show="tree", selectmode="browse")
        self.toc_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.toc_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.toc_tree.configure(yscrollcommand=scrollbar.set)
        self.toc_tree.bind("<<TreeviewSelect>>", on_toc_click)
