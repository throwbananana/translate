from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Sequence


class RetryActionStatus(str, Enum):
    SUCCESS = "success"
    SELECT_REQUIRED = "select_required"
    EMPTY_TRANSLATION = "empty_translation"
    CONFIG_LOCAL_MODEL = "config_local_model"
    CONFIG_API = "config_api"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


@dataclass
class RetryActionResult:
    status: RetryActionStatus
    message: str
    index: Optional[int] = None
    translated_text: Optional[str] = None


class RetryFailedSegmentService:
    """封装失败段落的重试与人工修正逻辑，减少 GUI 主类中的状态操作。"""

    def retry_failed_segment(
        self,
        *,
        selected_failed_index: Optional[int],
        failed_segments: list,
        translated_segments: list,
        api_type: str,
        api_configs: dict,
        custom_local_models: dict,
        openai_support: bool,
        translate_segment: Callable[[str, str], str],
        is_translation_incomplete: Callable[..., bool],
        target_language: str,
    ) -> RetryActionResult:
        target = self._get_selected_target(selected_failed_index, failed_segments, "请先选择需要重试的段落")
        if isinstance(target, RetryActionResult):
            return target

        validation = self._validate_retry_api(
            api_type=api_type,
            api_configs=api_configs,
            custom_local_models=custom_local_models,
            openai_support=openai_support,
        )
        if validation is not None:
            return validation

        info = target
        try:
            retry_text = translate_segment(api_type, info['source'])
        except Exception as e:
            return RetryActionResult(RetryActionStatus.FAILED, f"重试翻译失败: {e}")

        if is_translation_incomplete(retry_text, info['source'], target_language=target_language):
            return RetryActionResult(RetryActionStatus.INCOMPLETE, "重试后仍未完成，请手动翻译。")

        translated_segments[info['index']] = retry_text
        failed_segments.pop(selected_failed_index)
        return RetryActionResult(
            RetryActionStatus.SUCCESS,
            f"段 {info['index'] + 1} 已重新翻译并替换",
            index=info['index'],
            translated_text=retry_text,
        )

    def save_manual_translation(
        self,
        *,
        selected_failed_index: Optional[int],
        failed_segments: list,
        translated_segments: list,
        manual_text: str,
        translation_memory=None,
        target_language: str = "",
    ) -> RetryActionResult:
        target = self._get_selected_target(selected_failed_index, failed_segments, "请先选择需要替换的段落")
        if isinstance(target, RetryActionResult):
            return target

        manual_text = (manual_text or "").strip()
        if not manual_text:
            return RetryActionResult(RetryActionStatus.EMPTY_TRANSLATION, "手动翻译内容不能为空")

        info = target
        translated_segments[info['index']] = manual_text
        failed_segments.pop(selected_failed_index)

        if translation_memory is not None:
            try:
                translation_memory.store(
                    source_text=info['source'],
                    translated_text=manual_text,
                    target_lang=target_language,
                    api_provider="manual",
                    model="user_correction",
                    quality_score=100,
                )
                print(f"已将人工修正存入记忆库: ID={info['index']}")
            except Exception as e:
                print(f"保存到记忆库失败: {e}")

        return RetryActionResult(
            RetryActionStatus.SUCCESS,
            f"段 {info['index'] + 1} 已使用手动译文替换并存入记忆库",
            index=info['index'],
            translated_text=manual_text,
        )

    def _get_selected_target(self, selected_failed_index: Optional[int], failed_segments: Sequence[dict], empty_message: str):
        if selected_failed_index is None or not failed_segments:
            return RetryActionResult(RetryActionStatus.SELECT_REQUIRED, empty_message)
        if selected_failed_index < 0 or selected_failed_index >= len(failed_segments):
            return RetryActionResult(RetryActionStatus.SELECT_REQUIRED, empty_message)
        return failed_segments[selected_failed_index]

    def _validate_retry_api(self, *, api_type: str, api_configs: dict, custom_local_models: dict, openai_support: bool):
        if api_type in custom_local_models:
            config = custom_local_models[api_type]
            if not config.get('base_url') or not config.get('model_id'):
                return RetryActionResult(
                    RetryActionStatus.CONFIG_LOCAL_MODEL,
                    "请先配置本地模型的 Base URL 和 Model ID",
                )
            if not openai_support:
                return RetryActionResult(
                    RetryActionStatus.UNSUPPORTED,
                    "缺少 openai 库，无法调用本地模型",
                )
            return None

        config = api_configs.get(api_type, {})
        if api_type == 'custom' and not config.get('base_url'):
            return RetryActionResult(
                RetryActionStatus.CONFIG_API,
                "请先配置自定义API的 Base URL",
            )
        if api_type in ['gemini', 'openai', 'custom', 'lm_studio'] and not config.get('api_key'):
            return RetryActionResult(
                RetryActionStatus.CONFIG_API,
                "请先配置API Key",
            )
        if api_type == 'lm_studio' and not openai_support:
            return RetryActionResult(
                RetryActionStatus.UNSUPPORTED,
                "缺少 openai 库，无法调用本地LM Studio",
            )
        return None
