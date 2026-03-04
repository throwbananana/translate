#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation Memory Editor (TM Editor)
可视化管理翻译记忆库 (.db 文件)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

class TMEditorDialog:
    def __init__(self, parent, tm_instance):
        self.parent = parent
        self.tm = tm_instance
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("翻译记忆库编辑器 (Translation Memory)")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # 工具栏
        toolbar = ttk.Frame(self.dialog, padding=5)
        toolbar.pack(fill=tk.X)
        
        ttk.Label(toolbar, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        entry.pack(side=tk.LEFT, padx=5)
        entry.bind('<Return>', self.search_data)
        ttk.Button(toolbar, text="查询", command=self.search_data).pack(side=tk.LEFT)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        ttk.Button(toolbar, text="删除选中", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导出 CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="清空所有", command=self.clear_all).pack(side=tk.RIGHT, padx=5)

        # 列表区域
        list_frame = ttk.Frame(self.dialog, padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("id", "source", "target", "lang", "model", "score", "time")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("source", text="原文")
        self.tree.heading("target", text="译文")
        self.tree.heading("lang", text="目标语言")
        self.tree.heading("model", text="模型")
        self.tree.heading("score", text="分数")
        self.tree.heading("time", text="时间")
        
        self.tree.column("id", width=40, stretch=False)
        self.tree.column("source", width=300)
        self.tree.column("target", width=300)
        self.tree.column("lang", width=60, anchor="center")
        self.tree.column("model", width=80, anchor="center")
        self.tree.column("score", width=50, anchor="center")
        self.tree.column("time", width=120, anchor="center")
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 双击编辑
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # 状态栏
        self.status_var = tk.StringVar()
        ttk.Label(self.dialog, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)

    def load_data(self, query=None):
        """加载数据"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            conn = self.tm._get_conn()
            cursor = conn.cursor()
            
            if query:
                q = f"%{query}%"
                sql = "SELECT id, source_text, translated_text, target_lang, model, quality_score, timestamp FROM translations WHERE source_text LIKE ? OR translated_text LIKE ? ORDER BY id DESC LIMIT 500"
                cursor.execute(sql, (q, q))
            else:
                sql = "SELECT id, source_text, translated_text, target_lang, model, quality_score, timestamp FROM translations ORDER BY id DESC LIMIT 500"
                cursor.execute(sql)
                
            rows = cursor.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
                
            self.status_var.set(f"显示前 {len(rows)} 条记录")
            conn.close()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def search_data(self, event=None):
        self.load_data(self.search_var.get())

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        if not messagebox.askyesno("确认", f"确定删除选中的 {len(selected)} 条记录吗？"):
            return
            
        try:
            conn = self.tm._get_conn()
            cursor = conn.cursor()
            
            ids = [self.tree.item(item)['values'][0] for item in selected]
            cursor.executemany("DELETE FROM translations WHERE id=?", [(i,) for i in ids])
            
            conn.commit()
            conn.close()
            self.load_data()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def clear_all(self):
        if messagebox.askyesno("危险操作", "确定清空整个翻译记忆库吗？此操作不可恢复！"):
            self.tm.clear()
            self.load_data()

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not filename: return
        
        try:
            conn = self.tm._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM translations")
            rows = cursor.fetchall()
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([d[0] for d in cursor.description]) # Header
                writer.writerows(rows)
                
            messagebox.showinfo("成功", f"已导出 {len(rows)} 条记录")
            conn.close()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return
        
        values = self.tree.item(item)['values']
        self.edit_dialog(values)

    def edit_dialog(self, values):
        # values: id, source, target, lang, model, score, time
        record_id = values[0]
        
        win = tk.Toplevel(self.dialog)
        win.title(f"编辑记录 #{record_id}")
        win.geometry("500x400")
        
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="原文:").pack(anchor=tk.W)
        source_txt = tk.Text(frame, height=5, width=60)
        source_txt.insert("1.0", values[1])
        source_txt.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="译文:").pack(anchor=tk.W)
        target_txt = tk.Text(frame, height=5, width=60)
        target_txt.insert("1.0", values[2])
        target_txt.pack(fill=tk.X, pady=5)
        
        def save():
            new_source = source_txt.get("1.0", "end-1c").strip()
            new_target = target_txt.get("1.0", "end-1c").strip()
            
            if not new_source or not new_target:
                messagebox.showwarning("警告", "内容不能为空")
                return
                
            try:
                conn = self.tm._get_conn()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE translations SET source_text=?, translated_text=? WHERE id=?", 
                    (new_source, new_target, record_id)
                )
                conn.commit()
                conn.close()
                self.load_data(self.search_var.get())
                win.destroy()
            except Exception as e:
                messagebox.showerror("错误", str(e))
                
        ttk.Button(frame, text="保存修改", command=save).pack(pady=10)
