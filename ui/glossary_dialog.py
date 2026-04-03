#! python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


class GlossaryEditorDialog:
    """术语表编辑器对话框。"""

    def __init__(self, parent, glossary_manager):
        self.parent = parent
        self.gm = glossary_manager
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("术语表管理 (Glossary Manager)")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)

        self.current_glossary_name = "default"
        self.setup_ui()
        self.refresh_glossary_list()
        self.load_terms()

    def setup_ui(self):
        top_frame = ttk.Frame(self.dialog, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="选择术语表:").pack(side=tk.LEFT)
        self.glossary_combo = ttk.Combobox(top_frame, state="readonly", width=20)
        self.glossary_combo.pack(side=tk.LEFT, padx=5)
        self.glossary_combo.bind("<<ComboboxSelected>>", self.on_glossary_change)

        ttk.Button(top_frame, text="新建表", command=self.create_glossary).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="删除表", command=self.delete_glossary).pack(side=tk.LEFT, padx=2)

        ttk.Label(top_frame, text="搜索:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<KeyRelease>", self.filter_terms)

        list_frame = ttk.Frame(self.dialog, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("source", "target", "notes", "category")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("source", text="原文术语")
        self.tree.heading("target", text="目标翻译")
        self.tree.heading("notes", text="备注")
        self.tree.heading("category", text="分类")

        self.tree.column("source", width=200)
        self.tree.column("target", width=200)
        self.tree.column("notes", width=200)
        self.tree.column("category", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self.edit_term)

        btn_frame = ttk.Frame(self.dialog, padding=10)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="添加术语", command=self.add_term).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑选中", command=self.edit_term).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除选中", command=self.delete_term).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="刷新", command=self.load_terms).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def refresh_glossary_list(self):
        glossaries = self.gm.list_glossaries()
        names = [g["name"] for g in glossaries]
        if not names:
            self.gm.create_glossary("default", "默认术语表")
            names = ["default"]

        self.glossary_combo["values"] = names
        if self.current_glossary_name in names:
            self.glossary_combo.set(self.current_glossary_name)
        elif names:
            self.glossary_combo.set(names[0])
            self.current_glossary_name = names[0]

    def on_glossary_change(self, event):
        self.current_glossary_name = self.glossary_combo.get()
        self.load_terms()

    def load_terms(self):
        self.tree.delete(*self.tree.get_children())
        if not self.current_glossary_name:
            return

        self.gm.load_glossary(self.current_glossary_name)
        terms = self.gm.get_all_terms(self.current_glossary_name)

        query = self.search_var.get().lower()
        for term in terms:
            if query and (
                query not in term["source"].lower()
                and query not in term.get("target", "").lower()
            ):
                continue
            self.tree.insert(
                "",
                "end",
                values=(
                    term["source"],
                    term.get("target", ""),
                    term.get("notes", ""),
                    term.get("category", ""),
                ),
            )

    def filter_terms(self, event):
        self.load_terms()

    def add_term(self):
        self.edit_term_dialog(None)

    def edit_term(self, event=None):
        selected = self.tree.selection()
        if not selected and event is None:
            return
        if not selected:
            return

        item = self.tree.item(selected[0])
        values = item["values"]
        self.edit_term_dialog(
            {
                "source": values[0],
                "target": values[1],
                "notes": values[2],
                "category": values[3],
            }
        )

    def edit_term_dialog(self, term_data):
        is_edit = term_data is not None
        title = "编辑术语" if is_edit else "添加术语"

        edit_win = tk.Toplevel(self.dialog)
        edit_win.title(title)
        edit_win.geometry("400x300")
        edit_win.transient(self.dialog)
        edit_win.grab_set()

        frame = ttk.Frame(edit_win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="原文术语:").grid(row=0, column=0, sticky=tk.W, pady=5)
        source_var = tk.StringVar(value=term_data["source"] if is_edit else "")
        source_entry = ttk.Entry(frame, textvariable=source_var, width=30)
        source_entry.grid(row=0, column=1, pady=5)
        if is_edit:
            source_entry.config(state="readonly")

        ttk.Label(frame, text="目标翻译:").grid(row=1, column=0, sticky=tk.W, pady=5)
        target_var = tk.StringVar(value=term_data["target"] if is_edit else "")
        ttk.Entry(frame, textvariable=target_var, width=30).grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="备注:").grid(row=2, column=0, sticky=tk.W, pady=5)
        notes_var = tk.StringVar(value=term_data["notes"] if is_edit else "")
        ttk.Entry(frame, textvariable=notes_var, width=30).grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="分类:").grid(row=3, column=0, sticky=tk.W, pady=5)
        cat_var = tk.StringVar(value=term_data["category"] if is_edit else "")
        ttk.Entry(frame, textvariable=cat_var, width=30).grid(row=3, column=1, pady=5)

        def save():
            src = source_var.get().strip()
            tgt = target_var.get().strip()
            if not src or not tgt:
                messagebox.showwarning("错误", "原文和译文不能为空")
                return

            if is_edit:
                self.gm.update_term(
                    self.current_glossary_name,
                    src,
                    tgt,
                    notes_var.get(),
                    cat_var.get(),
                )
            else:
                self.gm.add_term(
                    self.current_glossary_name,
                    src,
                    tgt,
                    notes_var.get(),
                    cat_var.get(),
                )

            self.load_terms()
            edit_win.destroy()

        ttk.Button(frame, text="保存", command=save).grid(row=4, column=0, columnspan=2, pady=20)

    def delete_term(self):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        src = item["values"][0]

        if messagebox.askyesno("确认", f"确定删除术语 '{src}' 吗?"):
            self.gm.remove_term(self.current_glossary_name, src)
            self.load_terms()

    def create_glossary(self):
        name = simpledialog.askstring("新建术语表", "请输入术语表名称 (英文/数字):")
        if not name:
            return

        if self.gm.create_glossary(name):
            self.refresh_glossary_list()
            self.glossary_combo.set(name)
            self.on_glossary_change(None)
        else:
            messagebox.showerror("错误", "创建失败，可能名称已存在")

    def delete_glossary(self):
        name = self.current_glossary_name
        if name == "default":
            messagebox.showwarning("警告", "不能删除默认术语表")
            return

        if messagebox.askyesno("确认", f"确定删除术语表 '{name}' 吗? 此操作不可恢复!"):
            self.gm.delete_glossary(name)
            self.refresh_glossary_list()
            self.on_glossary_change(None)
