#! python
# -*- coding: utf-8 -*-
"""
列出可用的Gemini模型
"""

import google.generativeai as genai

# 使用提供的API key
api_key = "AIzaSyDsi7DlvrIS41MlfPLTEEwqxfTAsryjxmk"
genai.configure(api_key=api_key)

print("Available Gemini models:")
print("-" * 60)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model: {m.name}")
            print(f"  Display Name: {m.display_name}")
            print(f"  Description: {m.description}")
            print()
except Exception as e:
    print(f"Error: {e}")
