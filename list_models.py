#! python
# -*- coding: utf-8 -*-
"""列出当前账号可用的 Gemini 模型。"""

import os
import sys

import google.generativeai as genai


api_key = os.getenv("GEMINI_API_KEY", "").strip()
if not api_key:
    raise SystemExit("缺少环境变量 GEMINI_API_KEY，请先设置后再运行。")

genai.configure(api_key=api_key)

print("可用 Gemini 模型：")
print("-" * 60)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"模型: {m.name}")
            print(f"  显示名: {m.display_name}")
            print(f"  描述: {m.description}")
            print()
except Exception as e:
    print(f"错误: {e}")
    sys.exit(1)
