#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试翻译工作流
"""

import google.generativeai as genai
import re
import time

# 使用提供的API key
api_key = "AIzaSyDsi7DlvrIS41MlfPLTEEwqxfTAsryjxmk"
genai.configure(api_key=api_key)

# 创建测试文本文件
test_text = """Chapter 1: Introduction

This is a test book for translation.
We want to see how well the translation works.

Chapter 2: Testing

The translation tool should be able to handle multiple paragraphs.
It should preserve the formatting and structure of the original text.

This is another paragraph to test the segmentation functionality."""

# 保存测试文件
test_file = "test_book.txt"
with open(test_file, 'w', encoding='utf-8') as f:
    f.write(test_text)

print("=" * 60)
print("测试书籍翻译工作流")
print("=" * 60)
print(f"\n1. 已创建测试文件: {test_file}")
print(f"   字符数: {len(test_text)}")

# 2. 分段测试
def split_text_into_segments(text, max_length=500):
    """将文本分割成段落（复制自主程序）"""
    paragraphs = re.split(r'\n\s*\n', text)
    segments = []
    current_segment = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_segment) + len(para) + 2 <= max_length:
            if current_segment:
                current_segment += "\n\n" + para
            else:
                current_segment = para
        else:
            if current_segment:
                segments.append(current_segment)
            current_segment = para

    if current_segment:
        segments.append(current_segment)

    return segments

segments = split_text_into_segments(test_text, max_length=100)
print(f"\n2. 文本已分割成 {len(segments)} 段")
for i, seg in enumerate(segments, 1):
    print(f"   段落 {i} ({len(seg)} 字符): {seg[:50]}...")

# 3. 翻译测试
print("\n3. 开始翻译...")
model = genai.GenerativeModel('gemini-2.5-flash')

translated_segments = []
for idx, segment in enumerate(segments, 1):
    try:
        print(f"   翻译段落 {idx}/{len(segments)}...", end=' ')
        prompt = f"请将以下文本翻译成中文，保持原文的格式和段落结构:\n\n{segment}"
        response = model.generate_content(prompt)
        translated_segments.append(response.text)
        print("完成")
        time.sleep(0.5)  # 避免限流
    except Exception as e:
        print(f"失败: {e}")
        translated_segments.append(f"[翻译错误: {str(e)}]\n{segment}")

# 4. 合并译文
translated_text = "\n\n".join(translated_segments)
print(f"\n4. 翻译完成！译文长度: {len(translated_text)} 字符")

# 5. 导出测试
output_file = "test_book_translated.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(translated_text)
print(f"\n5. 译文已保存到: {output_file}")

# 6. 显示结果
print("\n" + "=" * 60)
print("原文:")
print("-" * 60)
print(test_text)
print("\n" + "=" * 60)
print("译文:")
print("-" * 60)
print(translated_text)
print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
