#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语法检查脚本
检查 book_translator_gui.pyw 是否有语法错误
"""

import py_compile
import sys

try:
    py_compile.compile('book_translator_gui.pyw', doraise=True)
    print("✓ 语法检查通过！")
    print("✓ 没有发现语法错误")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print("✗ 发现语法错误:")
    print(str(e))
    sys.exit(1)
