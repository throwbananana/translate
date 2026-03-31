import sys
from pathlib import Path

GUI_METHOD = """
    def _extract_json_object_from_response(self, response_text):
        \"\"\"从模型响应中尽量提取首个 JSON 对象。\"\"\"
        if not response_text:
            raise ValueError("AI 未返回内容")

        text = response_text.strip()

        # 去掉 Markdown 代码块包裹
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\\n".join(lines).strip()

        # 逐字符寻找第一个完整 JSON 对象
        start = text.find("{")
        if start == -1:
            raise ValueError("AI 未返回有效 JSON")

        depth = 0
        in_string = False
        escape = False

        for idx in range(start, len(text)):
            ch = text[idx]

            if escape:
                escape = False
                continue

            if ch == "\\\\" and in_string:
                escape = True
                continue

            if ch == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:idx + 1]

        raise ValueError("AI 返回中未找到完整 JSON 对象")

"""

TEST_FILE = """from pathlib import Path
import ast

GUI_PATH = Path(__file__).resolve().parent.parent / "book_translator_gui.pyw"

def test_gui_file_parses():
    source = GUI_PATH.read_text(encoding="utf-8")
    ast.parse(source)

def test_open_admin_audit_is_class_method():
    source = GUI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    gui_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "BookTranslatorGUI"
    )

    method_names = [node.name for node in gui_class.body if isinstance(node, ast.FunctionDef)]
    assert "open_admin_audit" in method_names

def test_json_extractor_exists():
    source = GUI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    gui_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "BookTranslatorGUI"
    )

    method_names = [node.name for node in gui_class.body if isinstance(node, ast.FunctionDef)]
    assert "_extract_json_object_from_response" in method_names
"""

def backup(path: Path):
    bak = path.with_name(path.name + ".bak_v3")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

def insert_json_helper(text: str) -> str:
    if "def _extract_json_object_from_response(self, response_text):" in text:
        return text

    anchor = "    def _analyze_with_custom_local_model(self, model_key, prompt):"
    if anchor not in text:
        raise RuntimeError("未找到插入 JSON helper 的锚点")
    return text.replace(anchor, GUI_METHOD + "\n" + anchor, 1)

def harden_json_extraction(text: str) -> str:
    old = """                    # 4. 解析 JSON
                    # 简单的 JSON 提取逻辑
                    try:
                        match = re.search(r'\\{.*\\}', response, re.DOTALL)
                        if not match:
                            raise ValueError(\"AI 未返回有效 JSON\")
                        json_str = match.group(0)
                        data = json.loads(json_str)

                        # 回到主线程更新 UI
                        self.root.after(0, lambda: update_ui(data))
                    except:
                        # 如果 AI 没返回标准 JSON，尝试简单的文本提取或报错
                        print(f\"AI Response (Raw): {response}\")
                        self.root.after(0, lambda: fail(\"AI 返回格式难以解析，请重试或手动填写。\"))"""
    new = """                    # 4. 解析 JSON（增强容错）
                    try:
                        json_str = self._extract_json_object_from_response(response)
                        data = json.loads(json_str)

                        # 回到主线程更新 UI
                        self.root.after(0, lambda: update_ui(data))
                    except Exception:
                        print(f\"AI Response (Raw): {response}\")
                        self.root.after(0, lambda: fail(\"AI 返回格式难以解析，请重试或手动填写。\"))"""
    if old in text:
        return text.replace(old, new, 1)

    if "self._extract_json_object_from_response(response)" in text:
        return text

    raise RuntimeError("未找到可替换的 JSON 解析代码块")

def fix_admin_method(text: str) -> str:
    nested_sig = "        def open_admin_audit(self):\n"
    class_sig = "    def open_admin_audit(self):\n"

    if class_sig in text and nested_sig not in text:
        return text

    if nested_sig not in text:
        raise RuntimeError("未找到嵌套的 open_admin_audit 定义")

    start = text.index(nested_sig)
    # 该方法之后紧跟 _build_global_search_ui
    next_anchor = "\n    def _build_global_search_ui(self, search_frame):\n"
    if next_anchor not in text[start:]:
        raise RuntimeError("未找到 open_admin_audit 方法的结束锚点")
    end = text.index(next_anchor, start)

    block = text[start:end]
    lines = block.splitlines()
    fixed_lines = []
    for line in lines:
        if line.startswith("        "):
            fixed_lines.append(line[4:])
        else:
            fixed_lines.append(line)
    fixed_block = "\n".join(fixed_lines).rstrip() + "\n"

    # 修复多行字符串
    broken = 图书馆管理功能未启用。
请通过环境变量 BOOK_TRANSLATOR_ADMIN_PASSWORD 或配置项 security.admin_password 设置管理员密码。
    good = 图书馆管理功能未启用。\n请通过环境变量 BOOK_TRANSLATOR_ADMIN_PASSWORD 或配置项 security.admin_password 设置管理员密码。
    fixed_block = fixed_block.replace(broken, good)

    # 删掉原嵌套块并在 _build_global_search_ui 前插入类级方法
    text = text[:start] + text[end:]
    insert_pos = text.index(next_anchor)
    text = text[:insert_pos] + "
" + fixed_block + text[insert_pos:]
    return text

def ensure_test_file(repo_root: Path):
    tests_dir = repo_root / "tests"
    tests_dir.mkdir(exist_ok=True)
    test_path = tests_dir / "test_gui_structure.py"
    if not test_path.exists():
        test_path.write_text(TEST_FILE, encoding="utf-8")

def main():
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    gui_path = repo_root / "book_translator_gui.pyw"
    if not gui_path.exists():
        raise SystemExit(f"未找到文件: {gui_path}")

    backup(gui_path)
    source = gui_path.read_text(encoding="utf-8")

    source = insert_json_helper(source)
    source = harden_json_extraction(source)
    source = fix_admin_method(source)

    gui_path.write_text(source, encoding="utf-8")
    ensure_test_file(repo_root)

    print("已修复:")
    print(f" - {gui_path}")
    print(f" - {repo_root / 'tests' / 'test_gui_structure.py'}")
    print("建议执行:")
    print("  py -m pytest tests/test_config_manager.py tests/test_gui_structure.py")

if __name__ == "__main__":
    main()
