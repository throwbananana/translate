import json

import pytest

from translation_engine import TranslationEngine
from tests.gui_test_utils import DummyRoot, DummyTree, DummyVar, load_gui_module


pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def gui_module():
    return load_gui_module()


def test_get_current_api_type_delegates_to_translation_selection(gui_module):
    gui = gui_module.BookTranslatorGUI.__new__(gui_module.BookTranslatorGUI)
    gui.get_translation_api_type = lambda: "local-qwen"

    assert gui.get_current_api_type() == "local-qwen"


def test_sync_engine_config_keeps_lm_studio_without_api_key(gui_module):
    gui = gui_module.BookTranslatorGUI.__new__(gui_module.BookTranslatorGUI)
    gui.api_configs = {
        "lm_studio": {
            "api_key": "",
            "base_url": "http://127.0.0.1:1234/v1",
            "model": "qwen",
            "temperature": 0.2,
        },
        "openai": {
            "api_key": "",
            "base_url": "",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
        },
    }
    gui.custom_local_models = {}
    gui.translation_engine = TranslationEngine()
    gui._provider_support_flags = lambda: {
        "gemini": True,
        "openai": True,
        "claude": True,
        "requests": True,
    }

    gui.sync_engine_config()

    assert "lm_studio" in gui.translation_engine.api_configs
    assert gui.translation_engine.fallback_provider == "lm_studio"


def test_browse_file_uses_file_processor_filters(gui_module, monkeypatch):
    captured = {}

    def fake_dialog(**kwargs):
        captured.update(kwargs)
        return "G:/book.docx"

    monkeypatch.setattr(gui_module.filedialog, "askopenfilename", fake_dialog)

    gui = gui_module.BookTranslatorGUI.__new__(gui_module.BookTranslatorGUI)
    gui.file_processor = type(
        "FakeFileProcessor",
        (),
        {"get_file_filter": lambda self: [("所有支持的文件", "*.txt *.docx *.md")]},
    )()
    gui.file_path_var = DummyVar()
    loaded = []
    gui.load_file_content = lambda path: loaded.append(path)

    gui.browse_file()

    assert captured["filetypes"] == [("所有支持的文件", "*.txt *.docx *.md")]
    assert gui.file_path_var.get() == "G:/book.docx"
    assert loaded == ["G:/book.docx"]


def test_try_resume_cached_progress_reads_via_file_processor(gui_module, monkeypatch, tmp_path):
    original_file = tmp_path / "book.pdf"
    original_file.write_text("example translated content", encoding="utf-8")
    content = "example translated content"
    signature = gui_module.BookTranslatorGUI.compute_text_signature(None, content)

    cache_file = tmp_path / "translation_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "file_path": str(original_file),
                "signature": signature,
                "source_segments": ["source-1", "source-2"],
                "translated_segments": ["译文-1"],
                "failed_segments": [],
                "resume_from_index": 1,
                "target_language": "中文",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class FakeFileProcessor:
        def __init__(self):
            self.calls = []

        def read_file(self, filepath, progress_callback=None):
            self.calls.append(filepath)
            if progress_callback:
                progress_callback("读取中")
            return content

    monkeypatch.setattr(gui_module.messagebox, "askyesno", lambda *args, **kwargs: True)

    gui = gui_module.BookTranslatorGUI.__new__(gui_module.BookTranslatorGUI)
    gui.root = DummyRoot()
    gui.file_processor = FakeFileProcessor()
    gui.progress_cache_path = cache_file
    gui.file_path_var = DummyVar()
    gui.progress_var = DummyVar(0)
    gui.progress_text_var = DummyVar("")
    gui.target_language_var = DummyVar("")
    gui.compute_text_signature = gui_module.BookTranslatorGUI.compute_text_signature.__get__(gui)
    gui.clear_progress_cache = lambda: None
    gui.update_translated_text = lambda text: None
    gui.refresh_failed_segments_view = lambda: None
    loaded = []
    gui.load_content_into_workspace = lambda **kwargs: loaded.append(kwargs)

    gui.try_resume_cached_progress()

    assert gui.file_processor.calls == [str(original_file)]
    assert loaded[0]["filepath"] == str(original_file)
    assert gui.translated_segments == ["译文-1"]
    assert gui.resume_from_index == 1


def test_refresh_search_tree_grouped_uses_group_source(gui_module):
    gui = gui_module.BookTranslatorGUI.__new__(gui_module.BookTranslatorGUI)
    gui.search_tree = DummyTree()
    gui.current_search_results = [
        {"title": "Book A", "author": "A", "source": "Anna's Archive", "category": "科幻"},
        {"title": "Book B", "author": "B", "source": "Z-Library", "category": "科幻"},
    ]

    gui._refresh_search_tree_grouped()

    group_call = next(call for call in gui.search_tree.insert_calls if call["iid"] == "group_0")
    assert group_call["values"][5] == "Anna's Archive"
