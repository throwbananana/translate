import pytest

from translation_review import (
    apply_manual_translation,
    is_translation_incomplete,
    verify_and_retry_segments,
)


pytestmark = pytest.mark.unit


def test_is_translation_incomplete_detects_untranslated_english_for_chinese():
    source = "This is a long English paragraph that should have been translated into Chinese."
    translated = "This is still mostly English and was not translated."

    assert is_translation_incomplete(translated, source, "中文") is True


def test_verify_and_retry_segments_retries_once_and_marks_remaining_failures():
    source_segments = ["hello world", "second paragraph"]
    translated_segments = ["", "still english"]

    def retry_callback(source, idx):
        if idx == 0:
            return "你好，世界"
        return "still english"

    updated_segments, failed = verify_and_retry_segments(
        source_segments,
        translated_segments,
        retry_callback,
        "中文",
    )

    assert updated_segments[0] == "你好，世界"
    assert updated_segments[1].startswith("[待手动翻译")
    assert failed == [{"index": 1, "source": "second paragraph", "last_error": "still english"}]


def test_apply_manual_translation_replaces_segment_and_removes_failed_item():
    translated_segments = ["第一段", "[待手动翻译 - 段 2]"]
    failed_segments = [{"index": 1, "source": "second paragraph", "last_error": "still english"}]

    updated_segments, updated_failed, info = apply_manual_translation(
        translated_segments,
        failed_segments,
        0,
        "第二段人工修正",
    )

    assert updated_segments == ["第一段", "第二段人工修正"]
    assert updated_failed == []
    assert info["source"] == "second paragraph"


def test_apply_manual_translation_rejects_empty_text():
    with pytest.raises(ValueError):
        apply_manual_translation(["x"], [{"index": 0, "source": "a", "last_error": ""}], 0, "   ")
