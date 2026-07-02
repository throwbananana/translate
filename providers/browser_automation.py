#! python
# -*- coding: utf-8 -*-
"""Playwright-backed browser provider.

This adapter sends prompts to a configured web chat page and reads the latest
assistant response from the DOM.  It is intentionally selector-driven because
web UIs change frequently and should not be treated like stable APIs.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import threading
import time
from typing import Any, Mapping

from app_paths import get_app_dir

from .base import ProviderRequest, ProviderResponse, coerce_timeout_seconds
from .errors import ProviderResponseError, ProviderTimeoutError


BROWSER_MODEL_PRESETS = {
    "custom": {
        "display_name": "自定义网页模型",
        "start_url": "",
        "browser": "chromium",
        "headless": False,
        "prompt_selector": "textarea, [contenteditable='true']",
        "submit_selector": "button[type='submit'], button[aria-label*='Send'], button[aria-label*='发送']",
        "response_selector": ".markdown, .prose, [data-message-author-role='assistant']",
        "timeout_seconds": 180,
        "settle_seconds": 3,
        "navigate_each_request": False,
    },
    "deepseek_web": {
        "display_name": "DeepSeek 网页端",
        "start_url": "https://chat.deepseek.com/",
        "browser": "chromium",
        "headless": False,
        "prompt_selector": "textarea, [contenteditable='true']",
        "submit_selector": "button[type='submit'], button[aria-label*='Send'], button[aria-label*='发送']",
        "response_selector": ".ds-markdown, .markdown, .prose",
        "timeout_seconds": 180,
        "settle_seconds": 3,
        "navigate_each_request": False,
    },
    "gemini_web": {
        "display_name": "Gemini 网页端",
        "start_url": "https://gemini.google.com/app",
        "browser": "chromium",
        "headless": False,
        "prompt_selector": "textarea, rich-textarea div.ql-editor[contenteditable='true']",
        "submit_selector": "button[aria-label*='Send'], button[aria-label*='发送'], button[type='submit']",
        "response_selector": "message-content, .markdown, .model-response-text, .prose",
        "timeout_seconds": 180,
        "settle_seconds": 3,
        "navigate_each_request": False,
    },
    "chatgpt_web": {
        "display_name": "ChatGPT 网页端",
        "start_url": "https://chatgpt.com/",
        "browser": "chromium",
        "headless": False,
        "prompt_selector": "#prompt-textarea",
        "submit_selector": "button[data-testid='send-button'], button[type='submit'], button[aria-label*='Send'], button[aria-label*='发送']",
        "response_selector": "[data-message-author-role='assistant']",
        "timeout_seconds": 180,
        "settle_seconds": 3,
        "navigate_each_request": False,
    },
}

LEGACY_BROWSER_MODEL_PRESET_ALIASES = {
    "gptinstant_web": "chatgpt_web",
}

LEGACY_BROWSER_MODEL_DEFAULTS = {
    "gptinstant_web": {
        "display_name": "GPTInstant 网页端",
        "start_url": "https://gptinstant.com/",
    },
}


def get_browser_model_preset(preset_name: str) -> dict[str, Any]:
    """Return a copy of a browser-model preset."""
    preset_name = LEGACY_BROWSER_MODEL_PRESET_ALIASES.get(preset_name, preset_name)
    return deepcopy(BROWSER_MODEL_PRESETS.get(preset_name) or BROWSER_MODEL_PRESETS["custom"])


def coerce_bool(value: Any, default: bool = False) -> bool:
    """Coerce config values that may come from JSON or tkinter."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "是", "启用"}


def normalize_browser_model_config(model_key: str, config: Mapping[str, Any]) -> dict[str, Any]:
    """Merge a browser model config with its selected preset."""
    raw_config = dict(config or {})
    raw_preset_name = raw_config.get("preset") or "custom"
    preset_name = LEGACY_BROWSER_MODEL_PRESET_ALIASES.get(raw_preset_name, raw_preset_name)
    if raw_preset_name in LEGACY_BROWSER_MODEL_DEFAULTS:
        legacy_defaults = LEGACY_BROWSER_MODEL_DEFAULTS[raw_preset_name]
        if raw_config.get("display_name") == legacy_defaults["display_name"]:
            raw_config.pop("display_name", None)
        if str(raw_config.get("start_url") or "").rstrip("/") == legacy_defaults["start_url"].rstrip("/"):
            raw_config.pop("start_url", None)
    merged = get_browser_model_preset(preset_name)
    merged.update(raw_config)
    merged["preset"] = preset_name
    merged["display_name"] = merged.get("display_name") or model_key
    merged["timeout_seconds"] = coerce_timeout_seconds(merged.get("timeout_seconds"))
    merged["settle_seconds"] = max(0.5, float(merged.get("settle_seconds") or 3))
    merged["headless"] = coerce_bool(merged.get("headless"), default=False)
    merged["navigate_each_request"] = coerce_bool(merged.get("navigate_each_request"), default=False)
    merged["browser"] = str(merged.get("browser") or "chromium").strip().lower()
    if not merged.get("user_data_dir"):
        merged["user_data_dir"] = str(get_app_dir() / "browser_profiles" / model_key)
    return merged


def build_browser_translation_prompt(request: ProviderRequest) -> str:
    """Build the prompt sent to a web chat page for translation."""
    base_prompt = (
        f"请将以下文本翻译成{request.target_lang}，保持原文的格式和段落结构。"
        "只输出翻译结果，不要添加解释、标题或代码块。"
    )
    parts = [part.strip() for part in (request.system_instruction, base_prompt, request.text) if part]
    return "\n\n".join(parts)


class BrowserAutomationProvider:
    """A selector-driven Playwright provider for web chat pages."""

    def __init__(self, model_key: str, config: Mapping[str, Any]):
        self.model_key = model_key
        self.config = normalize_browser_model_config(model_key, config)
        self.model = self.config.get("display_name") or model_key
        self.timeout_seconds = coerce_timeout_seconds(self.config.get("timeout_seconds"))
        self._lock = threading.RLock()
        self._playwright = None
        self._context = None
        self._page = None

    @classmethod
    def from_config(cls, model_key: str, config: Mapping[str, Any]) -> "BrowserAutomationProvider":
        return cls(model_key, config)

    def close(self) -> None:
        """Close the browser context if it is open."""
        with self._lock:
            if self._context is not None:
                try:
                    self._context.close()
                finally:
                    self._context = None
                    self._page = None
            if self._playwright is not None:
                try:
                    self._playwright.stop()
                finally:
                    self._playwright = None

    def translate(self, request: ProviderRequest) -> ProviderResponse:
        prompt = build_browser_translation_prompt(request)
        text = self.generate(prompt, timeout_seconds=request.timeout_seconds)
        return ProviderResponse(text=text, model=self.model)

    def generate(self, prompt: str, timeout_seconds: float | int | str | None = None) -> str:
        """Send a raw prompt and return the latest stable response text."""
        timeout = coerce_timeout_seconds(timeout_seconds or self.timeout_seconds)
        with self._lock:
            page = self._ensure_page(timeout)
            before_texts = self._response_texts(page)
            before_text = before_texts[-1] if before_texts else ""
            self._fill_prompt(page, prompt, timeout)
            self._submit_prompt(page, timeout)
            return self._wait_for_response(page, before_text, len(before_texts), timeout)

    def _ensure_page(self, timeout_seconds: float):
        if self._page is not None:
            if self.config.get("navigate_each_request"):
                self._page.goto(
                    self.config["start_url"],
                    wait_until="domcontentloaded",
                    timeout=int(timeout_seconds * 1000),
                )
            return self._page

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - covered through validation
            raise ImportError(
                "未安装 playwright，无法使用网页模型。请运行: pip install playwright && python -m playwright install chromium"
            ) from exc

        start_url = str(self.config.get("start_url") or "").strip()
        if not start_url:
            raise ProviderResponseError("网页模型缺少 start_url")

        user_data_dir = Path(self.config["user_data_dir"])
        user_data_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = sync_playwright().start()
        browser_name = self.config.get("browser") or "chromium"
        browser_type = getattr(self._playwright, browser_name, None)
        if browser_type is None:
            raise ProviderResponseError(f"不支持的浏览器类型: {browser_name}")

        self._context = browser_type.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=bool(self.config.get("headless")),
            viewport={"width": 1280, "height": 900},
        )
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self._page.goto(start_url, wait_until="domcontentloaded", timeout=int(timeout_seconds * 1000))
        return self._page

    def _prompt_locator(self, page):
        selector = str(self.config.get("prompt_selector") or "").strip()
        if not selector:
            raise ProviderResponseError("网页模型缺少 prompt_selector")
        return page.locator(selector).last

    def _response_locator(self, page):
        selector = str(self.config.get("response_selector") or "").strip()
        if not selector:
            raise ProviderResponseError("网页模型缺少 response_selector")
        return page.locator(selector)

    def _fill_prompt(self, page, prompt: str, timeout_seconds: float) -> None:
        locator = self._prompt_locator(page)
        timeout_ms = int(timeout_seconds * 1000)
        locator.wait_for(state="visible", timeout=timeout_ms)
        locator.click(timeout=timeout_ms)
        try:
            locator.fill(prompt, timeout=timeout_ms)
        except Exception:
            page.keyboard.press("Control+A")
            page.keyboard.type(prompt, delay=0)

    def _submit_prompt(self, page, timeout_seconds: float) -> None:
        selector = str(self.config.get("submit_selector") or "").strip()
        timeout_ms = int(timeout_seconds * 1000)
        if selector:
            submit = page.locator(selector).last
            submit.wait_for(state="visible", timeout=timeout_ms)
            submit.click(timeout=timeout_ms)
            return
        page.keyboard.press(str(self.config.get("submit_shortcut") or "Enter"))

    def _last_response_text(self, page) -> str:
        texts = self._response_texts(page)
        return texts[-1] if texts else ""

    def _response_texts(self, page) -> list[str]:
        try:
            texts = self._response_locator(page).all_inner_texts()
        except Exception:
            return []
        return [text.strip() for text in texts if text and text.strip()]

    def _wait_for_response(self, page, before_text: str, before_count: int, timeout_seconds: float) -> str:
        deadline = time.monotonic() + timeout_seconds
        settle_seconds = float(self.config.get("settle_seconds") or 3)
        last_text = ""
        stable_since = None
        saw_candidate = False

        while time.monotonic() < deadline:
            texts = self._response_texts(page)
            candidate = texts[-1] if texts else ""
            has_new_response = len(texts) > before_count
            if candidate and (has_new_response or candidate != before_text):
                if candidate != last_text:
                    last_text = candidate
                    stable_since = time.monotonic()
                    saw_candidate = True
                elif saw_candidate and stable_since and time.monotonic() - stable_since >= settle_seconds:
                    return candidate.strip()
            time.sleep(0.5)

        if last_text:
            return last_text.strip()
        raise ProviderTimeoutError("等待网页模型响应超时，请检查登录状态、选择器或网页是否仍在生成")
