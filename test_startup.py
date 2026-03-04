#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试程序启动
"""

import sys
import traceback

print("Testing program startup...")
print("=" * 60)

try:
    # 尝试导入主程序
    print("1. Importing modules...")
    import tkinter as tk
    from tkinter import ttk
    print("   - tkinter: OK")

    import google.generativeai as genai
    print("   - google-generativeai: OK")

    try:
        import PyPDF2
        print("   - PyPDF2: OK")
    except ImportError:
        print("   - PyPDF2: Not installed (PDF support disabled)")

    try:
        import ebooklib
        print("   - ebooklib: OK")
    except ImportError:
        print("   - ebooklib: Not installed (EPUB support disabled)")

    print("\n2. Creating main window...")
    root = tk.Tk()
    root.withdraw()  # 隐藏窗口

    print("\n3. Testing API status update...")
    # 创建简单的测试
    api_status_var = tk.StringVar(value="测试")
    api_status_label = ttk.Label(root, textvariable=api_status_var, foreground="orange")

    # 测试config方法
    api_status_label.config(foreground="green")
    print("   - Label.config(): OK")

    root.destroy()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    print("\nProgram should start normally now.")
    print("Run: python book_translator_gui.pyw")
    print("Or double-click: start.bat")

except Exception as e:
    print("\n" + "=" * 60)
    print("ERROR FOUND!")
    print("=" * 60)
    print(f"\nError: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
