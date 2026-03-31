from pathlib import Path
import re

p = Path("book_translator_gui.pyw")
text = p.read_text(encoding="utf-8")

pattern = re.compile(
    r'strict_json_prompt\s*=\s*\(\s*.*?\s*\+\s*prompt\s*\)',
    re.DOTALL
)

replacement = '''strict_json_prompt = (
                        "你是一个专业的图书管理员。请严格返回 JSON 对象，不要输出 Markdown 代码块，也不要附加解释。\\n\\n"
                        + prompt
                    )'''

new_text, count = pattern.subn(replacement, text, count=1)

if count != 1:
    raise SystemExit("[ERROR] strict_json_prompt block not found or not unique")

p.write_text(new_text, encoding="utf-8", newline="\\n")
print("[OK] fixed strict_json_prompt")
