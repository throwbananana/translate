#! python
# -*- coding: utf-8 -*-
"""
Format Converter Module
提供文件格式转换工具箱 (EPUB->TXT, PDF->Images, etc.)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import os

# Import existing handlers
try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    pass

try:
    from pdf2image import convert_from_path
except ImportError:
    pass

try:
    import PyPDF2
except ImportError:
    pass

class FormatConverterDialog:

    def __init__(self, parent, load_callback=None):

        self.parent = parent

        self.load_callback = load_callback

        

        self.dialog = tk.Toplevel(parent)

        self.dialog.title("格式转换工具箱 (Format Converter)")

        self.dialog.geometry("600x400")

        self.dialog.transient(parent)

        

        self.setup_ui()



    def setup_ui(self):

        # ... (Same as before)

        notebook = ttk.Notebook(self.dialog)

        notebook.pack(fill=tk.BOTH, expand=True, padding=10)

        

        # Tab 1: E-Book to Text

        tab1 = ttk.Frame(notebook)

        notebook.add(tab1, text="电子书转文本 (EPUB/PDF -> TXT)")

        self.setup_ebook_tab(tab1)

        

        # Tab 2: PDF to Images

        tab2 = ttk.Frame(notebook)

        notebook.add(tab2, text="PDF 转图片")

        self.setup_pdf_img_tab(tab2)

        

        # Status Bar

        self.status_var = tk.StringVar(value="就绪")

        ttk.Label(self.dialog, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)



    def setup_ebook_tab(self, parent):

        frame = ttk.Frame(parent, padding=20)

        frame.pack(fill=tk.BOTH, expand=True)

        

        ttk.Label(frame, text="源文件 (EPUB/PDF):").grid(row=0, column=0, sticky=tk.W)

        self.ebook_path = tk.StringVar()

        ttk.Entry(frame, textvariable=self.ebook_path, width=40).grid(row=0, column=1, padx=5)

        ttk.Button(frame, text="浏览...", command=lambda: self.browse_file(self.ebook_path, "*.epub *.pdf")).grid(row=0, column=2)

        

        ttk.Button(frame, text="开始转换", command=self.convert_ebook_to_txt).grid(row=1, column=1, pady=20)



    def setup_pdf_img_tab(self, parent):

        frame = ttk.Frame(parent, padding=20)

        frame.pack(fill=tk.BOTH, expand=True)

        

        ttk.Label(frame, text="源文件 (PDF):").grid(row=0, column=0, sticky=tk.W)

        self.pdf_path = tk.StringVar()

        ttk.Entry(frame, textvariable=self.pdf_path, width=40).grid(row=0, column=1, padx=5)

        ttk.Button(frame, text="浏览...", command=lambda: self.browse_file(self.pdf_path, "*.pdf")).grid(row=0, column=2)

        

        ttk.Label(frame, text="DPI (清晰度):").grid(row=1, column=0, sticky=tk.W)

        self.dpi_var = tk.StringVar(value="200")

        ttk.Entry(frame, textvariable=self.dpi_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5)

        

        ttk.Button(frame, text="开始转换", command=self.convert_pdf_to_images).grid(row=2, column=1, pady=20)



    def browse_file(self, var, types):

        f = filedialog.askopenfilename(filetypes=[("Files", types)])

        if f: var.set(f)



    def convert_ebook_to_txt(self):

        path = self.ebook_path.get()

        if not path or not os.path.exists(path):

            messagebox.showwarning("错误", "文件不存在")

            return

            

        ext = Path(path).suffix.lower()

        output = Path(path).with_suffix(".txt")

        

        self.status_var.set("正在转换...")

        

        def run():

            try:

                text = ""

                if ext == '.epub':

                    text = self._extract_epub(path)

                elif ext == '.pdf':

                    text = self._extract_pdf(path)

                else:

                    raise ValueError("不支持的格式")

                    

                with open(output, 'w', encoding='utf-8') as f:

                    f.write(text)

                    

                self.dialog.after(0, lambda: self._on_convert_success(output))

            except Exception as e:

                self.dialog.after(0, lambda: messagebox.showerror("失败", str(e)))

                self.dialog.after(0, lambda: self.status_var.set("失败"))

                

        threading.Thread(target=run, daemon=True).start()



    def _on_convert_success(self, output_path):

        self.status_var.set("转换完成")

        if messagebox.askyesno("转换成功", f"文件已保存到: {output_path}\n\n是否立即在翻译器中加载此文件？"):

            if self.load_callback:

                self.load_callback(str(output_path))

                self.dialog.destroy()

    def _extract_epub(self, path):
        book = epub.read_epub(path)
        texts = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            texts.append(soup.get_text())
        return "\n\n".join(texts)

    def _extract_pdf(self, path):
        # Use simple PyPDF2
        import PyPDF2
        texts = []
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                texts.append(page.extract_text() or "")
        return "\n\n".join(texts)

    def convert_pdf_to_images(self):
        path = self.pdf_path.get()
        if not path: return
        
        try:
            dpi = int(self.dpi_var.get())
        except:
            dpi = 200
        
        output_dir = filedialog.askdirectory(title="选择输出文件夹")
        if not output_dir: return
        
        self.status_var.set("正在转换图片...")
        
        def run():
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(path, dpi=dpi)
                base = Path(path).stem
                
                for i, img in enumerate(images):
                    out = Path(output_dir) / f"{base}_page_{i+1}.png"
                    img.save(out, "PNG")
                    self.dialog.after(0, lambda p=i: self.status_var.set(f"已保存第 {p+1} 页"))
                    
                self.dialog.after(0, lambda: messagebox.showinfo("成功", f"已转换 {len(images)} 张图片"))
                self.dialog.after(0, lambda: self.status_var.set("转换完成"))
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror("失败", f"转换失败 (可能未安装 Poppler):\n{e}"))
                
        threading.Thread(target=run, daemon=True).start()
