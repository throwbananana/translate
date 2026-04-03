import pytest

from file_processor import FileProcessor


pytestmark = pytest.mark.unit


def test_file_filter_includes_markdown_patterns():
    filters = FileProcessor.get_file_filter()
    patterns = " ".join(pattern for _, pattern in filters)

    assert "*.md" in patterns
    assert "*.markdown" in patterns


def test_file_filter_includes_docx_when_supported():
    supported = FileProcessor.get_supported_formats()
    filters = FileProcessor.get_file_filter()
    patterns = " ".join(pattern for _, pattern in filters)

    if ".docx" in supported:
        assert "*.docx" in patterns
