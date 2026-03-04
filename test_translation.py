#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试翻译功能
"""

import google.generativeai as genai

# 使用提供的API key
api_key = "AIzaSyDsi7DlvrIS41MlfPLTEEwqxfTAsryjxmk"
genai.configure(api_key=api_key)

# 创建模型
model = genai.GenerativeModel('gemini-2.5-flash')

# 测试文本
test_text = """
Hello, this is a test.
I want to translate this text to Chinese.
This is a simple test of the translation functionality.
"""

print("正在测试Gemini API翻译...")
print(f"原文:\n{test_text}\n")

try:
    prompt = f"请将以下文本翻译成中文，保持原文的格式和段落结构:\n\n{test_text}"
    response = model.generate_content(prompt)

    print("译文:")
    print(response.text)
    print("\n✓ 翻译成功!")

except Exception as e:
    print(f"✗ 翻译失败: {e}")
