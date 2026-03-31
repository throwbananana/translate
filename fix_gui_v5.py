from pathlib import Path
import shutil
import sys

repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
gui = repo / "book_translator_gui.pyw"
tests_dir = repo / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)
test_file = tests_dir / "test_gui_structure.py"

if not gui.exists():
    raise SystemExit(f"[ERROR] File not found: {gui}")

backup = gui.with_name(gui.name + ".bak_v5")
shutil.copy2(gui, backup)

text = gui.read_text(encoding="utf-8")

marker = "        def open_admin_audit(self):"
start = text.find(marker)
if start != -1:
    end_marker = "\n    def _build_global_search_ui(self, search_frame):"
    end = text.find(end_marker, start)
    if end == -1:
        raise RuntimeError("Could not locate end of nested open_admin_audit block")
    text = text[:start] + text[end:]

method = '''    def open_admin_audit(self):
        """打开管理员管理界面（用于删除记录）"""
        expected_password = (self.config_manager.get_admin_password() or "").strip()
        if not expected_password:
            messagebox.showwarning(
                "未启用",
                "图书馆管理功能未启用。\\n请通过环境变量 BOOK_TRANSLATOR_ADMIN_PASSWORD 或配置项 security.admin_password 设置管理员密码。"
            )
            return

        pwd = simpledialog.askstring("管理员登录", "请输入管理员密码:", show="*")
        if pwd is None:
            return
        if not hmac.compare_digest(pwd, expected_password):
            messagebox.showerror("错误", "密码错误")
            return

        audit_win = tk.Toplevel(self.root)
        audit_win.title("图书馆管理 (Library Admin)")
        audit_win.geometry("800x500")

        columns = ("id", "title", "uploader", "date", "status")
        tree = ttk.Treeview(audit_win, columns=columns, show="headings")
        tree.heading("id", text="ID")
        tree.heading("title", text="标题")
        tree.heading("uploader", text="上传者")
        tree.heading("date", text="日期")
        tree.heading("status", text="状态")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def refresh():
            tree.delete(*tree.get_children())
            books = self.community_manager.get_public_books()
            for b in books:
                tree.insert(
                    "",
                    "end",
                    values=(
                        b.get("id", ""),
                        b.get("title", ""),
                        b.get("uploader", ""),
                        b.get("date", ""),
                        b.get("status", "approved"),
                    ),
                )

        refresh()

        btn_frame = ttk.Frame(audit_win, padding=10)
        btn_frame.pack(fill=tk.X)

        def delete_entry():
            sel = tree.selection()
            if not sel:
                return
            bid = str(tree.item(sel[0])["values"][0])

            if messagebox.askyesno("确认", "确定从公共列表中删除此书籍吗？"):
                library = self.community_manager.get_public_books()
                new_library = [b for b in library if str(b.get("id", "")) != bid]
                self.community_manager._save_json(self.community_manager.library_file, new_library)
                messagebox.showinfo("成功", "已删除")
                refresh()
                self.refresh_community_list()

        ttk.Button(btn_frame, text="🗑️ 删除选中条目", command=delete_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="刷新", command=refresh).pack(side=tk.RIGHT, padx=5)
'''

if "\n    def open_admin_audit(self):\n" not in text:
    anchor = "\n    def _build_global_search_ui(self, search_frame):\n"
    idx = text.find(anchor)
    if idx == -1:
        raise RuntimeError("Could not locate insertion anchor")
    text = text[:idx] + "\n" + method + text[idx:]

gui.write_text(text, encoding="utf-8", newline="\n")

test_file.write_text(
    'from pathlib import Path\n\n'
    'def test_book_translator_gui_contains_open_admin_audit():\n'
    '    text = Path("book_translator_gui.pyw").read_text(encoding="utf-8")\n'
    '    assert "def open_admin_audit(self):" in text\n'
    '    assert "BOOK_TRANSLATOR_ADMIN_PASSWORD" in text\n',
    encoding="utf-8",
    newline="\n"
)

print(f"[OK] Updated: {gui}")
print(f"[OK] Backup:  {backup}")
print(f"[OK] Wrote:   {test_file}")
