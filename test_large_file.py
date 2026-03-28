#! python
# -*- coding: utf-8 -*-
"""
测试大文件加载
"""

# 生成不同大小的测试文件
test_sizes = [
    (1000, "1K字符"),
    (5000, "5K字符"),
    (10000, "10K字符"),
    (50000, "50K字符"),
    (100000, "100K字符"),
    (500000, "500K字符"),
]

for size, name in test_sizes:
    filename = f"test_{name.replace('K字符', 'k')}.txt"

    # 生成测试内容
    content = ""
    chapter = 1
    while len(content) < size:
        content += f"\nChapter {chapter}: Test Content\n\n"
        content += "This is test content for large file handling. " * 20
        content += "\n\n"
        chapter += 1

    content = content[:size]  # 截取到指定大小

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"OK 已创建 {filename} ({len(content):,} 字符)")

print("\n测试文件已创建，请尝试用翻译工具加载这些文件")
print("观察哪个文件大小会出现问题")
