#! python
# -*- coding: utf-8 -*-
"""手工测试：三种 Playwright 网页翻译流程。

该脚本用本地模拟网页验证 DeepSeek / Gemini / ChatGPT 三个网页端 preset 的
核心链路：打开网页、填写 prompt、提交、读取最新回复。
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from _common import OUTPUT_DIR
from providers.browser_automation import get_browser_model_preset
from translation_engine import TranslationEngine


TEST_TEXT = "Hello from the Playwright web translation flow."
TARGET_LANG = "中文"

WEB_TRANSLATION_FLOWS = [
    ("deepseek-web-smoke", "deepseek_web", "DeepSeek 网页端"),
    ("gemini-web-smoke", "gemini_web", "Gemini 网页端"),
    ("chatgpt-web-smoke", "chatgpt_web", "ChatGPT 网页端"),
]


def build_mock_page(flow_name: str) -> bytes:
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{flow_name} Mock</title>
</head>
<body>
  <main>
    <h1>{flow_name} Mock</h1>
    <form id="chat-form">
      <textarea id="prompt-textarea" data-testid="prompt" placeholder="Prompt"></textarea>
      <button type="submit" aria-label="Send">发送</button>
    </form>
    <section id="responses" aria-live="polite"></section>
  </main>
  <script>
    const flowName = {json.dumps(flow_name, ensure_ascii=False)};
    const form = document.querySelector("#chat-form");
    const promptBox = document.querySelector("[data-testid='prompt']");
    const responses = document.querySelector("#responses");

    form.addEventListener("submit", (event) => {{
      event.preventDefault();
      const prompt = promptBox.value;
      window.setTimeout(() => {{
        const response = document.createElement("div");
        response.className = "markdown ds-markdown prose";
        response.setAttribute("data-message-author-role", "assistant");
        response.textContent =
          `【${{flowName}}模拟译文】这是本地 Playwright 网页翻译测试返回的中文译文。` +
          (prompt.includes("Hello") ? "原文包含 Hello。" : "已收到翻译请求。");
        responses.appendChild(response);
      }}, 120);
    }});
  </script>
</body>
</html>
"""
    return html.encode("utf-8")


def make_handler():
    pages = {
        f"/{preset_name}": build_mock_page(display_name)
        for _, preset_name, display_name in WEB_TRANSLATION_FLOWS
    }

    class MockChatHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlparse(self.path).path
            body = pages.get(path)
            if body is None:
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    return MockChatHandler


def start_mock_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run_flow(engine: TranslationEngine, port: int, profile_root: str, key: str, preset_name: str, display_name: str):
    config = get_browser_model_preset(preset_name)
    config.update(
        {
            "display_name": display_name,
            "start_url": f"http://127.0.0.1:{port}/{preset_name}",
            "headless": True,
            "timeout_seconds": 20,
            "settle_seconds": 0.5,
            "user_data_dir": str(Path(profile_root) / key),
        }
    )

    engine.add_browser_model(key, config)
    result = engine.translate(
        TEST_TEXT,
        TARGET_LANG,
        provider=key,
        use_memory=False,
        use_glossary=False,
    )
    return result


def main():
    print("=" * 70)
    print("Playwright 网页翻译流程手工测试")
    print("=" * 70)
    print("本测试使用本地模拟网页，不访问真实网页端，也不需要 API Key。")

    server, thread = start_mock_server()
    port = server.server_address[1]
    records = []

    try:
        with TemporaryDirectory(
            prefix="book-translator-browser-smoke-",
            ignore_cleanup_errors=True,
        ) as profile_root:
            for key, preset_name, display_name in WEB_TRANSLATION_FLOWS:
                engine = TranslationEngine()
                print(f"\n[测试] {display_name} ({preset_name})")
                try:
                    result = run_flow(engine, port, profile_root, key, preset_name, display_name)
                finally:
                    engine.close_browser_providers()
                    time.sleep(0.5)

                record = {
                    "key": key,
                    "preset": preset_name,
                    "display_name": display_name,
                    "success": result.success,
                    "translated_text": result.translated_text,
                    "error": result.error,
                    "model": result.model,
                }
                records.append(record)

                if result.success:
                    print(f"[通过] {result.translated_text}")
                else:
                    print(f"[失败] {result.error}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

    output_path = OUTPUT_DIR / "browser_web_translation_report.json"
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[保存] 测试报告: {output_path}")

    failed = [record for record in records if not record["success"]]
    if failed:
        raise RuntimeError(f"{len(failed)} 个网页翻译流程失败，请查看报告。")

    print("\n全部网页翻译流程测试通过。")


if __name__ == "__main__":
    main()
