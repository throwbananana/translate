#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk


class LibraryPanel:
    """在线书城面板，负责全网搜索和社区图书馆的布局。"""

    def __init__(
        self,
        parent,
        on_sidebar_search_click,
        on_search_click,
        on_ai_search_click,
        on_open_online_config,
        on_search_result_select,
        on_prev_page,
        on_next_page,
        on_page_slider_release,
        on_auto_categorize_click,
        on_download_click,
        on_refresh_community_list,
        on_open_community_upload,
        on_open_admin_audit,
        on_download_community_book,
        on_copy_community_link,
    ):
        self.library_notebook = ttk.Notebook(parent)
        self.library_notebook.pack(fill=tk.BOTH, expand=True)

        search_tab_frame = ttk.Frame(self.library_notebook)
        self.library_notebook.add(search_tab_frame, text="全网搜索 (Z-Lib/Anna)")
        self._build_global_search_ui(
            search_tab_frame,
            on_sidebar_search_click=on_sidebar_search_click,
            on_search_click=on_search_click,
            on_ai_search_click=on_ai_search_click,
            on_open_online_config=on_open_online_config,
            on_search_result_select=on_search_result_select,
            on_prev_page=on_prev_page,
            on_next_page=on_next_page,
            on_page_slider_release=on_page_slider_release,
            on_auto_categorize_click=on_auto_categorize_click,
            on_download_click=on_download_click,
        )

        community_tab_frame = ttk.Frame(self.library_notebook)
        self.library_notebook.add(community_tab_frame, text="社区图书馆 (Community Library)")
        self._build_community_ui(
            community_tab_frame,
            on_refresh_community_list=on_refresh_community_list,
            on_open_community_upload=on_open_community_upload,
            on_open_admin_audit=on_open_admin_audit,
            on_download_community_book=on_download_community_book,
            on_copy_community_link=on_copy_community_link,
        )

    def _build_community_ui(
        self,
        parent,
        on_refresh_community_list,
        on_open_community_upload,
        on_open_admin_audit,
        on_download_community_book,
        on_copy_community_link,
    ):
        toolbar = ttk.Frame(parent, padding=10)
        toolbar.pack(fill=tk.X)

        ttk.Label(toolbar, text="📚 社区共享书籍", font=("", 12, "bold")).pack(side=tk.LEFT, padx=5)

        self.comm_status_var = tk.StringVar(value="就绪")
        ttk.Label(toolbar, textvariable=self.comm_status_var, foreground="gray").pack(side=tk.LEFT, padx=10)

        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="刷新列表", command=on_refresh_community_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📤 上传分享", command=on_open_community_upload).pack(side=tk.LEFT, padx=5)
        self.admin_btn = ttk.Button(btn_frame, text="🛡️ 图书馆管理", command=on_open_admin_audit)
        self.admin_btn.pack(side=tk.LEFT, padx=5)

        columns = ("title", "author", "description", "uploader", "size", "date")
        self.comm_tree = ttk.Treeview(parent, columns=columns, show="headings")
        self.comm_tree.heading("title", text="标题")
        self.comm_tree.heading("author", text="作者")
        self.comm_tree.heading("description", text="简介")
        self.comm_tree.heading("uploader", text="上传者")
        self.comm_tree.heading("size", text="大小")
        self.comm_tree.heading("date", text="日期")

        self.comm_tree.column("title", width=200)
        self.comm_tree.column("author", width=100)
        self.comm_tree.column("description", width=300)
        self.comm_tree.column("uploader", width=80)
        self.comm_tree.column("size", width=80)
        self.comm_tree.column("date", width=100)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.comm_tree.yview)
        self.comm_tree.configure(yscrollcommand=scrollbar.set)

        self.comm_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        self.comm_menu = tk.Menu(parent, tearoff=0)
        self.comm_menu.add_command(label="下载并导入", command=on_download_community_book)
        self.comm_menu.add_command(label="复制链接", command=on_copy_community_link)

        self.comm_tree.bind("<Button-3>", lambda event: self.comm_menu.post(event.x_root, event.y_root))
        self.comm_tree.bind("<Double-1>", lambda event: on_download_community_book())

    def _build_global_search_ui(
        self,
        search_frame,
        on_sidebar_search_click,
        on_search_click,
        on_ai_search_click,
        on_open_online_config,
        on_search_result_select,
        on_prev_page,
        on_next_page,
        on_page_slider_release,
        on_auto_categorize_click,
        on_download_click,
    ):
        paned = tk.PanedWindow(search_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True)

        sidebar_frame = ttk.Frame(paned, width=220)
        paned.add(sidebar_frame, minsize=180)

        cat_labelframe = ttk.LabelFrame(sidebar_frame, text="1. 分类 (按Ctrl多选)", padding="5")
        cat_labelframe.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.cat_tree = ttk.Treeview(cat_labelframe, show="tree", selectmode="extended", height=10)
        self.cat_tree.pack(fill=tk.BOTH, expand=True)

        categories = {
            "文学 (Fiction)": ["科幻 (Sci-Fi)", "奇幻 (Fantasy)", "悬疑 (Mystery)", "惊悚 (Thriller)", "浪漫 (Romance)", "经典 (Classics)"],
            "非虚构 (Non-Fiction)": ["历史 (History)", "传记 (Biography)", "哲学 (Philosophy)", "心理学 (Psychology)", "商业 (Business)"],
            "科技 (Tech)": ["计算机 (Computer Science)", "编程 (Programming)", "AI (Artificial Intelligence)", "物理 (Physics)", "数学 (Math)"],
            "生活 (Lifestyle)": ["烹饪 (Cooking)", "健康 (Health)", "旅游 (Travel)", "艺术 (Art)"],
            "漫画 (Comics)": ["Manga", "Graphic Novels"],
        }
        for main_cat, sub_cats in categories.items():
            parent = self.cat_tree.insert("", "end", text=main_cat, open=True)
            for sub in sub_cats:
                self.cat_tree.insert(parent, "end", text=sub)

        lang_labelframe = ttk.LabelFrame(sidebar_frame, text="2. 语言 (多选)", padding="5")
        lang_labelframe.pack(fill=tk.X, padx=2, pady=2)

        self.lang_vars = {}
        languages = [("中文", "zh"), ("英语", "en"), ("日语", "ja"), ("韩语", "ko"), ("法语", "fr"), ("德语", "de")]
        for i, (label, value) in enumerate(languages):
            var = tk.BooleanVar()
            self.lang_vars[value] = var
            ttk.Checkbutton(lang_labelframe, text=label, variable=var).grid(
                row=i // 2,
                column=i % 2,
                sticky="w",
                padx=2,
            )

        btn_frame = ttk.Frame(sidebar_frame, padding="5")
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="🔍 应用筛选并搜索", command=on_sidebar_search_click).pack(fill=tk.X)
        ttk.Label(btn_frame, text="提示: 结合顶部关键词更精准", font=("", 8), foreground="gray").pack(
            pady=(5, 0)
        )

        right_frame = ttk.Frame(paned, padding="10")
        paned.add(right_frame, minsize=600)
        self.search_frame = right_frame

        top_frame = ttk.Frame(right_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="附加关键词:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_query_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_query_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda event: on_search_click())

        self.search_source_var = tk.StringVar(value="Anna's Archive")
        source_combo = ttk.Combobox(
            top_frame,
            textvariable=self.search_source_var,
            values=["Anna's Archive", "Z-Library"],
            state="readonly",
            width=15,
        )
        source_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(top_frame, text="普通搜索", command=on_search_click).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="🤖 AI 寻书", command=on_ai_search_click).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="配置账号", command=on_open_online_config).pack(side=tk.LEFT, padx=5)

        list_frame = ttk.Frame(self.search_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("title", "author", "language", "ext", "size", "source", "category")
        self.search_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.search_tree.heading("title", text="标题")
        self.search_tree.heading("author", text="作者")
        self.search_tree.heading("language", text="语言")
        self.search_tree.heading("ext", text="格式")
        self.search_tree.heading("size", text="大小")
        self.search_tree.heading("source", text="来源")
        self.search_tree.heading("category", text="AI分类")

        self.search_tree.column("title", width=300)
        self.search_tree.column("author", width=120)
        self.search_tree.column("language", width=50, anchor="center")
        self.search_tree.column("ext", width=50, anchor="center")
        self.search_tree.column("size", width=70, anchor="e")
        self.search_tree.column("source", width=90, anchor="center")
        self.search_tree.column("category", width=100, anchor="center")

        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.search_tree.bind("<<TreeviewSelect>>", on_search_result_select)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_tree.config(yscrollcommand=scrollbar.set)

        pagination_frame = ttk.Frame(right_frame)
        pagination_frame.pack(fill=tk.X, pady=(5, 0))

        self.prev_btn = ttk.Button(pagination_frame, text="< 上一页", command=on_prev_page, state="disabled")
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.page_label_var = tk.StringVar(value="第 1 页")
        ttk.Label(pagination_frame, textvariable=self.page_label_var, width=8).pack(side=tk.LEFT, padx=5)

        self.page_slider = tk.Scale(pagination_frame, from_=1, to=50, orient=tk.HORIZONTAL, length=200, showvalue=0)
        self.page_slider.set(1)
        self.page_slider.pack(side=tk.LEFT, padx=5)
        self.page_slider.bind("<ButtonRelease-1>", on_page_slider_release)
        self.page_slider.bind("<Motion>", lambda event: self.page_label_var.set(f"第 {self.page_slider.get()} 页"))

        self.next_btn = ttk.Button(pagination_frame, text="下一页 >", command=on_next_page, state="disabled")
        self.next_btn.pack(side=tk.LEFT, padx=5)

        bottom_frame = ttk.LabelFrame(self.search_frame, text="结果详情", padding="10")
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        self.search_detail_var = tk.StringVar(value="请从左侧选择筛选条件或直接搜索")
        ttk.Label(bottom_frame, textvariable=self.search_detail_var, wraplength=800, justify=tk.LEFT).pack(
            fill=tk.X, pady=(0, 10)
        )

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="🏷️ 获取网站分类", command=on_auto_categorize_click).pack(side=tk.LEFT, padx=5)
        self.download_btn = ttk.Button(
            btn_frame,
            text="下载并导入翻译",
            command=on_download_click,
            state="disabled",
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)

        self.search_status_var = tk.StringVar(value="就绪")
        ttk.Label(self.search_frame, textvariable=self.search_status_var, foreground="gray").pack(
            side=tk.LEFT,
            pady=(5, 0),
        )
