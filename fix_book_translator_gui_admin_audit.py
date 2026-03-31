\
from pathlib import Path
import re
import shutil
import sys

REPLACEMENT = """\
    def open_admin_audit(self):
        \"\"\"打开管理员管理界面（用于删除记录）\"\"\"
        expected_password = (self.config_manager.get_admin_password() or \"\").strip()
        if not expected_password:
            messagebox.showwarning(
                \"未启用\",
                \"图书馆管理功能未启用。\\n请通过环境变量 BOOK_TRANSLATOR_ADMIN_PASSWORD 或配置项 security.admin_password 设置管理员密码。\"
            )
            return

        pwd = simpledialog.askstring(\"管理员登录\", \"请输入管理员密码:\", show=\"*\")
        if pwd is None:
            return
        if not hmac.compare_digest(pwd, expected_password):
            messagebox.showerror(\"错误\", \"密码错误\")
            return

        audit_win = tk.Toplevel(self.root)
        audit_win.title(\"图书馆管理 (Library Admin)\")
        audit_win.geometry(\"800x500\")

        columns = (\"id\", \"title\", \"uploader\", \"date\", \"status\")
        tree = ttk.Treeview(audit_win, columns=columns, show=\"headings\")
        tree.heading(\"id\", text=\"ID\")
        tree.heading(\"title\", text=\"标题\")
        tree.heading(\"uploader\", text=\"上传者\")
        tree.heading(\"date\", text=\"日期\")
        tree.heading(\"status\", text=\"状态\")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def refresh():
            tree.delete(*tree.get_children())
            books = self.community_manager.get_public_books()
            for book in books:
                tree.insert(
                    \"\",
                    \"end\",
                    values=(
                        book['id'],
                        book['title'],
                        book['uploader'],
                        book['date'],
                        book.get('status', 'approved'),
                    ),
                )

        refresh()

        btn_frame = ttk.Frame(audit_win, padding=10)
        btn_frame.pack(fill=tk.X)

        def delete_entry():
            sel = tree.selection()
            if not sel:
                return
            bid = str(tree.item(sel[0])['values'][0])

            if messagebox.askyesno(\"确认\", \"确定从公共列表中删除此书籍吗？\"):
                library = self.community_manager.get_public_books()
                new_library = [book for book in library if book['id'] != bid]
                self.community_manager._save_json(self.community_manager.library_file, new_library)

                messagebox.showinfo(\"成功\", \"已删除\")
                refresh()
                self.refresh_community_list()

        ttk.Button(btn_frame, text=\"🗑️ 删除选中条目\", command=delete_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=\"刷新\", command=refresh).pack(side=tk.RIGHT, padx=5)
"""

def main():
    if len(sys.argv) != 2:
        print("Usage: py fix_book_translator_gui_admin_audit.py book_translator_gui.pyw")
        raise SystemExit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        raise SystemExit(1)

    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\n\s{8}def open_admin_audit\(self\):.*?\n\s{4}def _build_global_search_ui\(self, search_frame\):",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        print("Could not locate the broken open_admin_audit block.")
        raise SystemExit(1)

    replacement = "\n" + REPLACEMENT + "\n\n    def _build_global_search_ui(self, search_frame):"
    new_text = text[:match.start()] + replacement + text[match.end():]

    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    path.write_text(new_text, encoding="utf-8")

    print(f"Patched: {path}")
    print(f"Backup : {backup}")

if __name__ == "__main__":
    main()
