#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""失败段落面板组件。"""

import tkinter as tk
from tkinter import ttk, scrolledtext


class FailedSegmentPanel:
    """封装失败段落标签页的控件与基础刷新逻辑。"""

    def __init__(
        self,
        parent_notebook,
        retry_api_var,
        api_names,
        on_select,
        on_retry,
        on_save_manual,
        on_open_retry_api,
    ):
        self.retry_api_var = retry_api_var
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="失败段落")

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
        self.failed_listbox.bind('<<ListboxSelect>>', on_select)

        detail_frame = ttk.Frame(self.frame)
        detail_frame.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(1, weight=1)
        detail_frame.rowconfigure(3, weight=1)

        ttk.Label(detail_frame, text="原文（只读）").grid(row=0, column=0, sticky=tk.W)
        self.failed_source_text = scrolledtext.ScrolledText(
            detail_frame,
            wrap=tk.WORD,
            height=6,
            state='disabled',
        )
        self.failed_source_text.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(0, 5))

        ttk.Label(detail_frame, text="手动翻译").grid(row=2, column=0, sticky=tk.W)
        self.manual_translation_text = scrolledtext.ScrolledText(
            detail_frame,
            wrap=tk.WORD,
            height=6,
        )
        self.manual_translation_text.grid(row=3, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        retry_api_frame = ttk.Frame(detail_frame)
        retry_api_frame.grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(retry_api_frame, text="重试API:").pack(side=tk.LEFT)
        self.retry_api_combo = ttk.Combobox(
            retry_api_frame,
            textvariable=self.retry_api_var,
            values=api_names,
            state='readonly',
            width=22,
        )
        self.retry_api_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(retry_api_frame, text="配置", command=on_open_retry_api).pack(side=tk.LEFT)

        button_frame = ttk.Frame(detail_frame)
        button_frame.grid(row=5, column=0, sticky=tk.E, pady=(5, 0))
        ttk.Button(button_frame, text="重试翻译", command=on_retry).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="保存手动翻译", command=on_save_manual).grid(row=0, column=1, padx=5)

        self.failed_status_var = tk.StringVar(value="暂无失败段落")
        ttk.Label(self.frame, textvariable=self.failed_status_var).grid(
            row=2,
            column=0,
            columnspan=3,
            sticky=tk.W,
            pady=(5, 0),
        )

    def populate_failed_segments(self, failed_segments):
        self.failed_listbox.delete(0, tk.END)
        self.clear_detail()

        if not failed_segments:
            self.failed_status_var.set("暂无失败段落")
            return

        for item in failed_segments:
            snippet = item['source'].replace('\n', ' ')
            if len(snippet) > 60:
                snippet = snippet[:60] + "..."
            self.failed_listbox.insert(tk.END, f"段 {item['index'] + 1}: {snippet}")

        self.failed_status_var.set(f"待处理段落: {len(failed_segments)} 个")

    def clear_detail(self):
        self.failed_source_text.config(state='normal')
        self.failed_source_text.delete('1.0', tk.END)
        self.failed_source_text.config(state='disabled')
        self.manual_translation_text.delete('1.0', tk.END)

    def show_failed_source(self, source_text):
        self.failed_source_text.config(state='normal')
        self.failed_source_text.delete('1.0', tk.END)
        self.failed_source_text.insert('1.0', source_text)
        self.failed_source_text.config(state='disabled')
        self.manual_translation_text.delete('1.0', tk.END)

    def get_selected_index(self):
        selection = self.failed_listbox.curselection()
        if not selection:
            return None
        return selection[0]

    def get_manual_translation(self):
        return self.manual_translation_text.get('1.0', tk.END).strip()

    def set_retry_api_names(self, api_names):
        self.retry_api_combo['values'] = api_names
