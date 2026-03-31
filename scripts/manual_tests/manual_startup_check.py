#! python
# -*- coding: utf-8 -*-
"""手工测试：程序启动检查。"""

import sys
import traceback


print("测试程序启动...")
print("=" * 60)

try:
    print("1. 导入基础模块...")
    import tkinter as tk
    from tkinter import ttk

    print("   - tkinter: OK")

    try:
        import google.generativeai  # noqa: F401

        print("   - google-generativeai: OK")
    except ImportError:
        print("   - google-generativeai: 未安装")

    try:
        import PyPDF2  # noqa: F401

        print("   - PyPDF2: OK")
    except ImportError:
        print("   - PyPDF2: 未安装（PDF 支持关闭）")

    try:
        import ebooklib  # noqa: F401

        print("   - ebooklib: OK")
    except ImportError:
        print("   - ebooklib: 未安装（EPUB 支持关闭）")

    print("\n2. 创建主窗口...")
    root = tk.Tk()
    root.withdraw()

    print("\n3. 检查状态标签更新...")
    api_status_var = tk.StringVar(value="测试")
    api_status_label = ttk.Label(root, textvariable=api_status_var, foreground="orange")
    api_status_label.config(foreground="green")
    print("   - Label.config(): OK")

    root.destroy()

    print("\n" + "=" * 60)
    print("启动检查通过。")
    print("=" * 60)
except Exception as exc:
    print("\n" + "=" * 60)
    print("启动检查失败")
    print("=" * 60)
    print(f"\n错误: {exc}")
    print("\n完整堆栈:")
    traceback.print_exc()
    sys.exit(1)
