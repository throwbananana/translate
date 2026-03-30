from __future__ import annotations

import pathlib
import re
import shutil
import sys
from datetime import datetime


def detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def replace_once(text: str, pattern: str, repl: str, desc: str, flags: int = re.MULTILINE | re.DOTALL) -> str:
    new_text, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"未能定位需要修改的代码块: {desc}")
    return new_text


def main() -> int:
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("book_translator_gui.pyw")
    if not target.exists():
        print(f"未找到文件: {target}")
        return 1

    original = target.read_text(encoding="utf-8")
    newline = detect_newline(original)
    text = original

    # 1) import hmac
    text = replace_once(
        text,
        r"from copy import deepcopy\r?\nimport hashlib",
        "from copy import deepcopy" + newline + "import hmac" + newline + "import hashlib",
        "导入 hmac",
        flags=re.MULTILINE,
    )

    # 2) 在 call_api_for_analysis 后插入通用文本生成辅助方法
    helper = (
        '            raise ValueError(f"不支持的解析API类型: {api_type}")' + newline + newline +
        '    def generate_text_with_selected_api(self, prompt, preferred_api_type=None):' + newline +
        '        """使用当前选中的解析 API 进行通用文本生成。"""' + newline +
        '        api_type = preferred_api_type or self.get_analysis_api_type()' + newline + newline +
        '        if api_type in self.custom_local_models:' + newline +
        '            return self._analyze_with_custom_local_model(api_type, prompt)' + newline +
        "        elif api_type == 'gemini':" + newline +
        '            return self._analyze_with_gemini(prompt)' + newline +
        "        elif api_type == 'openai':" + newline +
        '            return self._analyze_with_openai(prompt)' + newline +
        "        elif api_type == 'custom':" + newline +
        '            return self._analyze_with_custom_api(prompt)' + newline +
        "        elif api_type == 'lm_studio':" + newline +
        '            return self._analyze_with_lm_studio(prompt)' + newline +
        '        else:' + newline +
        '            raise ValueError(f"不支持的文本生成 API 类型: {api_type}")' + newline + newline +
        '    def _analyze_with_custom_local_model(self, model_key, prompt):'
    )
    text = replace_once(
        text,
        r"\s+raise ValueError\(f\"不支持的解析API类型: \{api_type\}\"\)\r?\n\r?\n\s+def _analyze_with_custom_local_model\(self, model_key, prompt\):",
        newline + helper,
        "插入 generate_text_with_selected_api 辅助方法",
    )

    # 3) 修复 AI 自动识别元数据时对 translation_engine.translate 的错误调用
    replacement_block = (
        '                    # 3. 调用当前选中的文本生成 API' + newline +
        '                    api_type = self.get_analysis_api_type()' + newline +
        "                    if api_type not in self.custom_local_models and not self.api_configs.get(api_type, {}).get('api_key'):" + newline +
        '                        api_type = self.get_translation_api_type()' + newline + newline +
        '                    strict_json_prompt = (' + newline +
        '                        "你是一个专业的图书管理员。请严格返回 JSON 对象，不要输出 Markdown 代码块，也不要附加解释。\\n\\n"' + newline +
        '                        + prompt' + newline +
        '                    )' + newline +
        '                    response = self.generate_text_with_selected_api(strict_json_prompt, preferred_api_type=api_type)'
    )
    text = replace_once(
        text,
        r"\s+# 3\. 调用翻译引擎 \(复用当前配置的解析/翻译API\).*?response = self\.translation_engine\.translate\(\r?\n\s+text=prompt,\r?\n\s+source_lang=\"Auto\",\r?\n\s+target_lang=\"JSON\", # Hint for JSON\r?\n\s+api_type=api_type,\r?\n\s+api_config=self\.api_configs\[api_type\]\r?\n\s+\)",
        newline + replacement_block,
        "修复 AI 元数据自动识别调用",
    )

    # 4) 强化 JSON 提取
    text = replace_once(
        text,
        r"\s+json_str = re\.search\(r'\\\{\.\*\\\}', response, re\.DOTALL\)\.group\(0\)\r?\n\s+data = json\.loads\(json_str\)",
        newline + '                        match = re.search(r\'\\{.*\\}\', response, re.DOTALL)' + newline +
        '                        if not match:' + newline +
        '                            raise ValueError("AI 未返回有效 JSON")' + newline +
        '                        json_str = match.group(0)' + newline +
        '                        data = json.loads(json_str)',
        "强化 JSON 提取逻辑",
    )

    # 5) 去掉硬编码管理员密码
    admin_repl = (
        '    def open_admin_audit(self):' + newline +
        '        """打开管理员管理界面（用于删除记录）"""' + newline +
        '        expected_password = (self.config_manager.get_admin_password() or "").strip()' + newline +
        '        if not expected_password:' + newline +
        '            messagebox.showwarning(' + newline +
        '                "未启用",' + newline +
        '                "图书馆管理功能未启用。\\n请通过环境变量 BOOK_TRANSLATOR_ADMIN_PASSWORD 或配置项 security.admin_password 设置管理员密码。"' + newline +
        '            )' + newline +
        '            return' + newline + newline +
        '        pwd = simpledialog.askstring("管理员登录", "请输入管理员密码:", show="*")' + newline +
        '        if pwd is None:' + newline +
        '            return' + newline +
        '        if not hmac.compare_digest(pwd, expected_password):' + newline +
        '            messagebox.showerror("错误", "密码错误")' + newline +
        '            return'
    )
    text = replace_once(
        text,
        r"def open_admin_audit\(self\):\r?\n\s+\"\"\"打开管理员管理界面（用于删除记录）\"\"\"\r?\n\s+pwd = simpledialog\.askstring\(\"管理员登录\", \"请输入管理员密码:\", show=\"\*\"\)\r?\n\s+if pwd != \"admin\":\r?\n\s+messagebox\.showerror\(\"错误\", \"密码错误\"\)\r?\n\s+return",
        admin_repl,
        "替换硬编码管理员密码",
    )

    if text == original:
        print("没有检测到需要修改的内容。")
        return 1

    backup = target.with_suffix(target.suffix + ".bak." + datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(target, backup)
    target.write_text(text, encoding="utf-8", newline="")

    print(f"已修复: {target}")
    print(f"已备份: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
