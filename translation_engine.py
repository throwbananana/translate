#! python
# -*- coding: utf-8 -*-
"""
翻译引擎 (Translation Engine) 模块
封装所有翻译相关的逻辑，支持多种API和翻译策略

功能：
- 多API提供商支持 (Gemini, OpenAI, Claude, DeepSeek, 自定义)
- 翻译记忆集成
- 术语表集成
- 翻译质量评估
- 批量翻译
- 流式翻译
- 自动重试和降级
"""

import re
import time
from typing import Optional, Dict, List, Callable, Generator, Any
from dataclasses import dataclass
from enum import Enum

# API 支持检测
try:
    import google.generativeai as genai
    GEMINI_SUPPORT = True
except ImportError:
    GEMINI_SUPPORT = False

try:
    import openai
    OPENAI_SUPPORT = True
except ImportError:
    OPENAI_SUPPORT = False

try:
    import anthropic
    CLAUDE_SUPPORT = True
except ImportError:
    CLAUDE_SUPPORT = False

try:
    import requests
    REQUESTS_SUPPORT = True
except ImportError:
    REQUESTS_SUPPORT = False


class APIProvider(Enum):
    """API 提供商枚举"""
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    LM_STUDIO = "lm_studio"
    CUSTOM = "custom"


@dataclass
class TranslationResult:
    """翻译结果"""
    source_text: str
    translated_text: str
    target_lang: str
    provider: str
    model: str
    quality_score: int = 0
    from_memory: bool = False
    tokens_used: int = 0
    time_taken: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and bool(self.translated_text)


@dataclass
class APIConfig:
    """API 配置"""
    provider: APIProvider
    api_key: str
    model: str
    base_url: str = ""
    temperature: float = 0.2
    max_tokens: int = 4096


class TranslationEngine:
    """翻译引擎"""

    # 配额/限流错误关键词
    QUOTA_ERROR_KEYWORDS = [
        'quota', 'rate limit', 'rate_limit', 'resource_exhausted',
        '429', 'insufficient_quota', 'quota exceeded', 'rate_limit_exceeded',
        'too many requests', 'overloaded'
    ]

    def __init__(self):
        """初始化翻译引擎"""
        self.api_configs: Dict[str, APIConfig] = {}
        self.custom_local_models: Dict[str, Dict] = {}
        self.fallback_provider: Optional[str] = None
        self.translation_memory = None
        self.glossary_manager = None

        # 回调函数
        self.on_progress: Optional[Callable[[str], None]] = None
        self.on_translation_complete: Optional[Callable[[TranslationResult], None]] = None

    def set_translation_memory(self, tm):
        """设置翻译记忆实例"""
        self.translation_memory = tm

    def set_glossary_manager(self, gm):
        """设置术语表管理器实例"""
        self.glossary_manager = gm

    def add_api_config(self, name: str, config: APIConfig):
        """添加 API 配置"""
        self.api_configs[name] = config

    def add_custom_local_model(self, name: str, display_name: str,
                               base_url: str, model_id: str,
                               api_key: str = "lm-studio"):
        """添加自定义本地模型"""
        self.custom_local_models[name] = {
            'display_name': display_name,
            'base_url': base_url,
            'model_id': model_id,
            'api_key': api_key
        }

    def set_fallback_provider(self, provider_name: str):
        """设置降级时使用的提供商"""
        self.fallback_provider = provider_name

    def _is_builtin_config_ready(self, provider: str) -> bool:
        config = self.api_configs.get(provider)
        if not config:
            return False

        if provider == 'gemini':
            return GEMINI_SUPPORT and bool(config.api_key and config.model)
        if provider == 'openai':
            return OPENAI_SUPPORT and bool(config.api_key and config.model)
        if provider == 'claude':
            return CLAUDE_SUPPORT and bool(config.api_key and config.model)
        if provider == 'deepseek':
            return OPENAI_SUPPORT and bool(config.api_key and config.model)
        if provider == 'lm_studio':
            return OPENAI_SUPPORT and bool(config.base_url and config.model)
        if provider == 'custom':
            return REQUESTS_SUPPORT and bool(config.base_url and config.model)
        return False

    def _is_custom_local_model_ready(self, provider: str) -> bool:
        config = self.custom_local_models.get(provider)
        return OPENAI_SUPPORT and bool(config and config.get('base_url') and config.get('model_id'))

    def _select_provider(self, provider: Optional[str]) -> str:
        if provider is not None:
            if provider in self.custom_local_models and self._is_custom_local_model_ready(provider):
                return provider
            if provider in self.api_configs and self._is_builtin_config_ready(provider):
                return provider
            raise ValueError(f'提供商未配置完成或当前环境不可用: {provider}')

        available = self.get_available_providers()
        if not available:
            raise ValueError('没有可用的翻译提供商')
        return available[0]

    def get_available_providers(self) -> List[str]:
        """获取可用的翻译提供商列表"""
        providers = []

        for provider in ('gemini', 'openai', 'claude', 'lm_studio', 'custom', 'deepseek'):
            if self._is_builtin_config_ready(provider):
                providers.append(provider)

        for provider in self.custom_local_models:
            if self._is_custom_local_model_ready(provider):
                providers.append(provider)

        return providers

    def translate(self, text: str, target_lang: str,
                  provider: str = None,
                  use_memory: bool = True,
                  use_glossary: bool = True,
                  context: str = None,
                  extra_prompt: str = "",
                  max_retries: int = 3,
                  retry_count: int = 0) -> TranslationResult:
        """
        翻译文本

        Args:
            text: 源文本
            target_lang: 目标语言
            provider: 使用的翻译提供商
            use_memory: 是否使用翻译记忆
            use_glossary: 是否使用术语表
            context: 上下文信息
            extra_prompt: 额外的提示词（如风格指导）
            max_retries: 最大重试次数
            retry_count: 当前重试次数

        Returns:
            翻译结果
        """
        start_time = time.time()

        # 检查翻译记忆
        if use_memory and self.translation_memory:
            cached = self.translation_memory.lookup(text, target_lang)
            if cached:
                return TranslationResult(
                    source_text=text,
                    translated_text=cached,
                    target_lang=target_lang,
                    provider="memory",
                    model="cache",
                    from_memory=True,
                    time_taken=time.time() - start_time
                )

        # 确定使用的提供商
        try:
            provider = self._select_provider(provider)
        except ValueError as exc:
            return TranslationResult(
                source_text=text,
                translated_text="",
                target_lang=target_lang,
                provider=provider or "none",
                model="",
                error=str(exc)
            )

        # 获取术语表提示
        glossary_prompt = ""
        if use_glossary and self.glossary_manager:
            glossary_prompt = self.glossary_manager.generate_prompt_injection(text)
            
        # 组合提示词 parts
        prompt_parts = []
        if extra_prompt:
            prompt_parts.append(extra_prompt)
        if context:
            prompt_parts.append(f"\n【上下文参考】\n上一段译文：{context}\n请在翻译时保持与上下文的连贯性。")
        if glossary_prompt:
            prompt_parts.append(glossary_prompt)
            
        final_system_instruction = "\n\n".join(prompt_parts)

        # 执行翻译
        try:
            translated, model_used = self._do_translate(
                text, target_lang, provider, final_system_instruction
            )

            result = TranslationResult(
                source_text=text,
                translated_text=translated,
                target_lang=target_lang,
                provider=provider,
                model=model_used,
                time_taken=time.time() - start_time
            )

            # 评估质量
            result.quality_score = self.evaluate_quality(text, translated, target_lang)

            # 存入翻译记忆
            if use_memory and self.translation_memory and result.success:
                self.translation_memory.store(
                    text, translated, target_lang,
                    api_provider=provider,
                    model=model_used,
                    quality_score=result.quality_score
                )

            return result

        except Exception as e:
            error_msg = str(e).lower()

            # 检查是否为配额错误
            is_quota_error = any(
                kw in error_msg for kw in self.QUOTA_ERROR_KEYWORDS
            )
            
            # 自动重试逻辑
            if is_quota_error and retry_count < max_retries:
                # 尝试解析建议的等待时间
                wait_time = 5 * (2 ** retry_count) # 默认指数退避
                match = re.search(r"retry in (\d+(\.\d+)?)s", str(e))
                if match:
                    wait_time = float(match.group(1)) + 1.0 # 额外加1秒缓冲
                
                # 限制最大等待时间 (例如 60秒)
                wait_time = min(wait_time, 60.0)

                msg = f"API 限流 ({provider})，{wait_time:.1f}秒后重试 ({retry_count + 1}/{max_retries})..."
                if self.on_progress:
                    self.on_progress(msg)
                else:
                    print(f"[Engine] {msg}") # Fallback logging
                
                time.sleep(wait_time)
                return self.translate(
                    text, target_lang,
                    provider=provider,
                    use_memory=use_memory,
                    use_glossary=use_glossary,
                    context=context,
                    extra_prompt=extra_prompt,
                    max_retries=max_retries,
                    retry_count=retry_count + 1
                )

            # 尝试降级
            if is_quota_error and self.fallback_provider and provider != self.fallback_provider:
                if self.on_progress:
                    self.on_progress(f"API 配额用尽，切换到 {self.fallback_provider}...")

                return self.translate(
                    text, target_lang,
                    provider=self.fallback_provider,
                    use_memory=use_memory,
                    use_glossary=use_glossary,
                    context=context,
                    extra_prompt=extra_prompt
                )

            return TranslationResult(
                source_text=text,
                translated_text="",
                target_lang=target_lang,
                provider=provider,
                model="",
                error=str(e),
                time_taken=time.time() - start_time
            )

    def _do_translate(self, text: str, target_lang: str,
                      provider: str, glossary_prompt: str = "") -> tuple:
        """
        执行实际的翻译调用

        Returns:
            (翻译结果, 模型名称) 元组
        """
        # 检查是否为自定义本地模型
        if provider in self.custom_local_models:
            return self._translate_with_custom_local(text, target_lang, provider, glossary_prompt)

        if provider == 'gemini':
            return self._translate_with_gemini(text, target_lang, glossary_prompt)
        elif provider == 'openai':
            return self._translate_with_openai(text, target_lang, glossary_prompt)
        elif provider == 'claude':
            return self._translate_with_claude(text, target_lang, glossary_prompt)
        elif provider == 'deepseek':
            return self._translate_with_deepseek(text, target_lang, glossary_prompt)
        elif provider == 'lm_studio':
            return self._translate_with_lm_studio(text, target_lang, glossary_prompt)
        elif provider == 'custom':
            return self._translate_with_custom_api(text, target_lang, glossary_prompt)
        else:
            raise ValueError(f"不支持的翻译提供商: {provider}")

    def _build_prompt(self, text: str, target_lang: str, glossary_prompt: str = "") -> str:
        """构建翻译提示词"""
        base_prompt = f"请将以下文本翻译成{target_lang}，保持原文的格式和段落结构。只输出翻译结果，不要添加任何解释。"

        if glossary_prompt:
            return f"{glossary_prompt}{base_prompt}\n\n{text}"
        return f"{base_prompt}\n\n{text}"

    def _translate_with_gemini(self, text: str, target_lang: str,
                               glossary_prompt: str = "") -> tuple:
        """使用 Gemini API 翻译"""
        if not GEMINI_SUPPORT:
            raise ImportError("未安装 google-generativeai")

        config = self.api_configs.get('gemini')
        if not config:
            raise ValueError("未配置 Gemini API")

        genai.configure(api_key=config.api_key)
        model = genai.GenerativeModel(config.model)

        prompt = self._build_prompt(text, target_lang, glossary_prompt)
        response = model.generate_content(prompt)

        return response.text, config.model

    def _translate_with_openai(self, text: str, target_lang: str,
                               glossary_prompt: str = "") -> tuple:
        """使用 OpenAI API 翻译"""
        if not OPENAI_SUPPORT:
            raise ImportError("未安装 openai")

        config = self.api_configs.get('openai')
        if not config:
            raise ValueError("未配置 OpenAI API")

        client_kwargs = {'api_key': config.api_key}
        if config.base_url:
            client_kwargs['base_url'] = config.base_url

        client = openai.OpenAI(**client_kwargs)

        system_prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{target_lang}，保持原文的格式和段落结构。"
        if glossary_prompt:
            system_prompt = f"{glossary_prompt}{system_prompt}"

        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=config.temperature
        )

        return response.choices[0].message.content, config.model

    def _translate_with_claude(self, text: str, target_lang: str,
                               glossary_prompt: str = "") -> tuple:
        """使用 Claude API 翻译"""
        if not CLAUDE_SUPPORT:
            raise ImportError("未安装 anthropic")

        config = self.api_configs.get('claude')
        if not config:
            raise ValueError("未配置 Claude API")

        client = anthropic.Anthropic(api_key=config.api_key)

        system_prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{target_lang}，保持原文的格式和段落结构。"
        if glossary_prompt:
            system_prompt = f"{glossary_prompt}{system_prompt}"

        message = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": text}
            ]
        )

        return message.content[0].text, config.model

    def _translate_with_deepseek(self, text: str, target_lang: str,
                                 glossary_prompt: str = "") -> tuple:
        """使用 DeepSeek API 翻译"""
        if not OPENAI_SUPPORT:
            raise ImportError("未安装 openai")

        config = self.api_configs.get('deepseek')
        if not config:
            raise ValueError("未配置 DeepSeek API")

        # DeepSeek 使用 OpenAI 兼容接口
        client = openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://api.deepseek.com/v1"
        )

        system_prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{target_lang}，保持原文的格式和段落结构。"
        if glossary_prompt:
            system_prompt = f"{glossary_prompt}{system_prompt}"

        response = client.chat.completions.create(
            model=config.model or "deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=config.temperature
        )

        return response.choices[0].message.content, config.model

    def _translate_with_lm_studio(self, text: str, target_lang: str,
                                  glossary_prompt: str = "") -> tuple:
        """使用本地 LM Studio 翻译"""
        if not OPENAI_SUPPORT:
            raise ImportError("未安装 openai")

        config = self.api_configs.get('lm_studio')
        if not config:
            raise ValueError("未配置 LM Studio")

        client = openai.OpenAI(
            api_key=config.api_key or "lm-studio",
            base_url=config.base_url or "http://127.0.0.1:1234/v1"
        )

        system_prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{target_lang}，保持原文的格式和段落结构。"
        if glossary_prompt:
            system_prompt = f"{glossary_prompt}{system_prompt}"

        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=config.temperature
        )

        return response.choices[0].message.content, config.model

    def _translate_with_custom_api(self, text: str, target_lang: str,
                                   glossary_prompt: str = "") -> tuple:
        """使用自定义 API 翻译"""
        if not REQUESTS_SUPPORT:
            raise ImportError("未安装 requests")

        config = self.api_configs.get('custom')
        if not config:
            raise ValueError("未配置自定义 API")

        url = f"{config.base_url.rstrip('/')}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.api_key}'
        }

        system_prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{target_lang}，保持原文的格式和段落结构。"
        if glossary_prompt:
            system_prompt = f"{glossary_prompt}{system_prompt}"

        data = {
            'model': config.model,
            'messages': [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            'temperature': config.temperature
        }

        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result['choices'][0]['message']['content'], config.model

    def _translate_with_custom_local(self, text: str, target_lang: str,
                                     model_key: str, glossary_prompt: str = "") -> tuple:
        """使用自定义本地模型翻译"""
        if not OPENAI_SUPPORT:
            raise ImportError("未安装 openai")

        config = self.custom_local_models.get(model_key)
        if not config:
            raise ValueError(f"未找到本地模型: {model_key}")

        client = openai.OpenAI(
            api_key=config.get('api_key', 'lm-studio'),
            base_url=config['base_url']
        )

        system_prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{target_lang}，保持原文的格式和段落结构。"
        if glossary_prompt:
            system_prompt = f"{glossary_prompt}{system_prompt}"

        response = client.chat.completions.create(
            model=config['model_id'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.2
        )

        return response.choices[0].message.content, config['model_id']

    def translate_stream(self, text: str, target_lang: str,
                         provider: str = None) -> Generator[str, None, None]:
        """
        流式翻译（实时返回翻译结果）

        Args:
            text: 源文本
            target_lang: 目标语言
            provider: 翻译提供商

        Yields:
            翻译结果片段
        """
        try:
            provider = self._select_provider(provider)
        except ValueError as exc:
            yield f"[错误: {exc}]"
            return

        # 获取术语表提示
        glossary_prompt = ""
        if self.glossary_manager:
            glossary_prompt = self.glossary_manager.generate_prompt_injection(text)

        try:
            if provider in ['openai', 'lm_studio', 'deepseek'] or provider in self.custom_local_models:
                yield from self._stream_openai_compatible(
                    text, target_lang, provider, glossary_prompt
                )
            else:
                # 不支持流式的提供商，直接返回完整结果
                result = self.translate(text, target_lang, provider)
                if result.success:
                    yield result.translated_text
                else:
                    yield f"[错误: {result.error}]"

        except Exception as e:
            yield f"[错误: {str(e)}]"

    def _stream_openai_compatible(self, text: str, target_lang: str,
                                  provider: str, glossary_prompt: str = "") -> Generator[str, None, None]:
        """OpenAI 兼容 API 的流式翻译"""
        if provider in self.custom_local_models:
            config = self.custom_local_models[provider]
            client = openai.OpenAI(
                api_key=config.get('api_key', 'lm-studio'),
                base_url=config['base_url']
            )
            model = config['model_id']
        else:
            api_config = self.api_configs.get(provider)
            if not api_config:
                yield f"[错误: 未配置 {provider}]"
                return

            client_kwargs = {'api_key': api_config.api_key}
            if api_config.base_url:
                client_kwargs['base_url'] = api_config.base_url

            client = openai.OpenAI(**client_kwargs)
            model = api_config.model

        system_prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{target_lang}，保持原文的格式和段落结构。"
        if glossary_prompt:
            system_prompt = f"{glossary_prompt}{system_prompt}"

        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def translate_batch(self, texts: List[str], target_lang: str,
                        provider: str = None,
                        on_progress: Callable[[int, int], None] = None,
                        delay: float = 0.5) -> List[TranslationResult]:
        """
        批量翻译

        Args:
            texts: 源文本列表
            target_lang: 目标语言
            provider: 翻译提供商
            on_progress: 进度回调 (current, total)
            delay: 每次翻译后的延迟（秒）

        Returns:
            翻译结果列表
        """
        results = []
        total = len(texts)

        for idx, text in enumerate(texts):
            result = self.translate(text, target_lang, provider)
            results.append(result)

            if on_progress:
                on_progress(idx + 1, total)

            if delay > 0 and idx < total - 1:
                time.sleep(delay)

        return results

    def evaluate_quality(self, source: str, translated: str,
                         target_lang: str) -> int:
        """
        评估翻译质量

        Args:
            source: 源文本
            translated: 翻译结果
            target_lang: 目标语言

        Returns:
            质量分数 (0-100)
        """
        if not translated or not translated.strip():
            return 0

        score = 100
        normalized = translated.strip()

        # 检查错误标记
        if any(marker in normalized for marker in ['[翻译错误', '[未翻译', '[待手动翻译']):
            return 0

        # 长度检查
        if len(normalized) < 5:
            return 10

        # 是否与原文相同（未翻译）
        if normalized == source.strip():
            return 20

        # 长度比例检查
        target_is_chinese = any(kw in target_lang.lower() for kw in ['中文', '汉语', 'chinese', 'zh'])
        expected_ratio = 0.5 if target_is_chinese else 1.0

        actual_ratio = len(normalized) / len(source) if source else 0
        ratio_diff = abs(actual_ratio - expected_ratio)

        if ratio_diff > 0.5:
            score -= 30
        elif ratio_diff > 0.3:
            score -= 15

        # 语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', normalized))
        latin_chars = len(re.findall(r'[A-Za-z]', normalized))
        total_chars = len(re.findall(r'\S', normalized)) or 1

        chinese_ratio = chinese_chars / total_chars
        latin_ratio = latin_chars / total_chars

        if target_is_chinese:
            if chinese_ratio < 0.3:
                score -= 40
            elif chinese_ratio < 0.5:
                score -= 20
        else:
            if latin_ratio < 0.3 and len(source) > 50:
                score -= 40

        # 格式保留检查
        source_newlines = source.count('\n')
        trans_newlines = normalized.count('\n')

        if source_newlines > 3 and trans_newlines == 0:
            score -= 10

        return max(0, min(100, score))

    def is_translation_incomplete(self, source: str, translated: str,
                                   target_lang: str) -> bool:
        """
        检测翻译是否不完整

        Args:
            source: 源文本
            translated: 翻译结果
            target_lang: 目标语言

        Returns:
            是否不完整
        """
        return self.evaluate_quality(source, translated, target_lang) < 50

    def test_connection(self, provider: str) -> tuple:
        """
        测试 API 连接

        Args:
            provider: 提供商名称

        Returns:
            (成功, 消息) 元组
        """
        try:
            result = self.translate(
                "Hello",
                "中文",
                provider=provider,
                use_memory=False,
                use_glossary=False
            )

            if result.success:
                return True, f"连接成功！响应: {result.translated_text[:50]}"
            else:
                return False, f"连接失败: {result.error}"

        except Exception as e:
            return False, f"连接错误: {str(e)}"


# 便捷函数
def create_engine_with_config(config: dict) -> TranslationEngine:
    """
    从配置字典创建翻译引擎

    Args:
        config: 配置字典，格式与 translator_config.json 相同

    Returns:
        配置好的翻译引擎
    """
    engine = TranslationEngine()

    api_configs = config.get('api_configs', {})

    for name, cfg in api_configs.items():
        if not cfg.get('api_key'):
            continue

        provider = APIProvider.GEMINI  # 默认
        if name == 'gemini':
            provider = APIProvider.GEMINI
        elif name == 'openai':
            provider = APIProvider.OPENAI
        elif name == 'claude':
            provider = APIProvider.CLAUDE
        elif name == 'deepseek':
            provider = APIProvider.DEEPSEEK
        elif name == 'lm_studio':
            provider = APIProvider.LM_STUDIO
        elif name == 'custom':
            provider = APIProvider.CUSTOM

        engine.add_api_config(name, APIConfig(
            provider=provider,
            api_key=cfg.get('api_key', ''),
            model=cfg.get('model', ''),
            base_url=cfg.get('base_url', ''),
            temperature=cfg.get('temperature', 0.2)
        ))

    # 自定义本地模型
    for name, cfg in config.get('custom_local_models', {}).items():
        engine.add_custom_local_model(
            name=name,
            display_name=cfg.get('display_name', name),
            base_url=cfg.get('base_url', ''),
            model_id=cfg.get('model_id', ''),
            api_key=cfg.get('api_key', 'lm-studio')
        )

    # 设置降级提供商
    if 'lm_studio' in api_configs and api_configs['lm_studio'].get('api_key'):
        engine.set_fallback_provider('lm_studio')
    elif engine.custom_local_models:
        engine.set_fallback_provider(list(engine.custom_local_models.keys())[0])

    return engine


if __name__ == '__main__':
    # 测试代码
    print("翻译引擎模块测试")
    print("=" * 50)

    engine = TranslationEngine()

    # 测试可用提供商
    providers = engine.get_available_providers()
    print(f"\n可用提供商: {providers}")

    print(f"Gemini 支持: {GEMINI_SUPPORT}")
    print(f"OpenAI 支持: {OPENAI_SUPPORT}")
    print(f"Claude 支持: {CLAUDE_SUPPORT}")

    # 测试质量评估
    print("\n质量评估测试:")
    test_cases = [
        ("Hello, world!", "你好，世界！", "中文"),
        ("Hello, world!", "Hello, world!", "中文"),  # 未翻译
        ("Hello, world!", "", "中文"),  # 空翻译
        ("This is a long text.", "这是一段长文本。", "中文"),
    ]

    for source, translated, target in test_cases:
        score = engine.evaluate_quality(source, translated, target)
        incomplete = engine.is_translation_incomplete(source, translated, target)
        print(f"  '{source}' -> '{translated}' | 分数: {score} | 不完整: {incomplete}")

    print("\n测试完成!")
