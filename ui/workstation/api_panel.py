#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk


class ApiPanel:
    """API 配置区域。"""

    LANG_OPTIONS = ["中文", "英文", "English", "日语", "韩语", "德语", "法语"]
    STYLE_OPTIONS = [
        "直译 (Literal)",
        "通俗小说 (Novel)",
        "学术专业 (Academic)",
        "武侠/古风 (Wuxia)",
        "新闻/媒体 (News)",
    ]

    def __init__(
        self,
        parent,
        api_names,
        translation_api_var,
        analysis_api_var,
        target_language_var,
        config_manager,
        on_api_type_change,
        on_open_translation_config,
        on_open_analysis_config,
        on_add_local_model,
        on_manage_local_models,
        on_update_concurrency_label,
    ):
        self.frame = ttk.LabelFrame(parent, text="API配置", padding="10")
        self.frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.frame.columnconfigure(1, weight=1)

        ttk.Label(self.frame, text="翻译API:").grid(row=0, column=0, sticky=tk.W)
        self.translation_api_combo = ttk.Combobox(
            self.frame,
            textvariable=translation_api_var,
            values=api_names,
            state="readonly",
            width=22,
        )
        self.translation_api_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.translation_api_combo.bind("<<ComboboxSelected>>", on_api_type_change)
        ttk.Button(self.frame, text="配置", command=on_open_translation_config).grid(
            row=0,
            column=2,
            padx=5,
        )

        ttk.Label(self.frame, text="解析API:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.analysis_api_combo = ttk.Combobox(
            self.frame,
            textvariable=analysis_api_var,
            values=api_names,
            state="readonly",
            width=22,
        )
        self.analysis_api_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=(5, 0))
        ttk.Button(self.frame, text="配置", command=on_open_analysis_config).grid(
            row=1,
            column=2,
            padx=5,
            pady=(5, 0),
        )

        model_btn_frame = ttk.Frame(self.frame)
        model_btn_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(8, 0))
        ttk.Button(model_btn_frame, text="+ 添加本地模型", command=on_add_local_model).pack(
            side=tk.LEFT,
            padx=(0, 5),
        )
        ttk.Button(model_btn_frame, text="管理本地模型", command=on_manage_local_models).pack(side=tk.LEFT)

        self.api_status_var = tk.StringVar(value="未配置")
        self.api_status_label = ttk.Label(
            self.frame,
            textvariable=self.api_status_var,
            foreground="orange",
        )
        self.api_status_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        ttk.Label(self.frame, text="目标语言:").grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        self.lang_combo = ttk.Combobox(
            self.frame,
            textvariable=target_language_var,
            values=self.LANG_OPTIONS,
            state="normal",
            width=22,
        )
        self.lang_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=(5, 0))

        self.style_var = tk.StringVar(
            value=config_manager.get("translation_style", "通俗小说 (Novel)")
        )
        ttk.Label(self.frame, text="翻译风格:").grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        self.style_combo = ttk.Combobox(
            self.frame,
            textvariable=self.style_var,
            values=self.STYLE_OPTIONS,
            state="readonly",
            width=22,
        )
        self.style_combo.grid(row=5, column=1, sticky=tk.W, padx=5, pady=(5, 0))

        ttk.Label(self.frame, text="并发线程:").grid(row=6, column=0, sticky=tk.W, pady=(5, 0))
        concurrency_frame = ttk.Frame(self.frame)
        concurrency_frame.grid(row=6, column=1, columnspan=2, sticky=tk.W, pady=(5, 0))

        self.concurrency_var = tk.IntVar(value=config_manager.get("concurrency", 1))
        self.concurrency_scale = tk.Scale(
            concurrency_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.concurrency_var,
            length=140,
            showvalue=0,
            command=on_update_concurrency_label,
        )
        self.concurrency_scale.pack(side=tk.LEFT, padx=(5, 5))

        self.concurrency_label = ttk.Label(
            concurrency_frame,
            text=f"{self.concurrency_var.get()} (高质量模式)",
        )
        self.concurrency_label.pack(side=tk.LEFT)

        self.concurrency_hint_var = tk.StringVar(value="")
        ttk.Label(
            self.frame,
            textvariable=self.concurrency_hint_var,
            foreground="gray",
            font=("", 8),
        ).grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))

        ttk.Label(
            self.frame,
            text="API配额用尽时将自动切换到本地模型",
            foreground="gray",
            font=("", 8),
        ).grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
