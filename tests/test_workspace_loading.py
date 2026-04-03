import pytest

from tests.gui_test_utils import DummyVar, DummyWidget, load_gui_module


pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def gui_module():
    return load_gui_module()


def build_gui(gui_module):
    gui = gui_module.BookTranslatorGUI.__new__(gui_module.BookTranslatorGUI)
    gui.file_path_var = DummyVar("")
    gui.progress_var = DummyVar(0)
    gui.progress_text_var = DummyVar("")
    gui.file_info_var = DummyVar("")
    gui.cost_var = DummyVar("")
    gui.analysis_status_var = DummyVar("")
    gui.translated_text_widget = DummyWidget()
    gui.toggle_preview_btn = DummyWidget()
    gui.analysis_text = DummyWidget()
    gui.analysis_listbox = DummyWidget()
    gui.original_text = DummyWidget()
    gui.preview_limit = 100
    gui.show_full_text = True
    gui.api_configs = {"gemini": {"model": "gemini-2.5-flash"}}
    gui.get_translation_api_type = lambda: "gemini"
    gui.refresh_failed_segments_view = lambda: None
    gui.update_comparison_view = lambda: None
    gui.compute_text_signature = gui_module.BookTranslatorGUI.compute_text_signature.__get__(gui)
    gui.docx_handler = object()
    return gui


def test_load_content_into_workspace_resets_runtime_state(gui_module):
    gui = build_gui(gui_module)
    gui.source_segments = ["old"]
    gui.translated_segments = ["old translated"]
    gui.failed_segments = [{"index": 0}]
    gui.analysis_segments = ["old analysis"]
    gui.current_text = ""
    gui.generate_toc = lambda content: setattr(gui, "toc_snapshot", content[:5])
    gui._init_docx_handler_if_needed = lambda filepath: setattr(gui, "docx_init_arg", filepath)
    gui.clear_progress_cache = lambda: setattr(gui, "cache_cleared", True)

    info = gui.load_content_into_workspace(
        title="Clipboard Content",
        content="hello world",
        filepath=None,
        clear_progress_cache=False,
    )

    assert gui.file_path_var.get() == "Clipboard Content"
    assert gui.current_text == "hello world"
    assert gui.source_segments == []
    assert gui.translated_segments == []
    assert gui.failed_segments == []
    assert gui.analysis_segments == []
    assert gui.show_full_text is False
    assert gui.toc_snapshot == "hello"
    assert info["char_count"] == 11
    assert "预估成本" in gui.cost_var.get()


def test_load_content_into_workspace_calls_docx_init_and_clears_cache(gui_module):
    gui = build_gui(gui_module)
    gui.generate_toc = lambda content: None
    gui.clear_progress_cache = lambda: setattr(gui, "cache_cleared", True)
    gui._init_docx_handler_if_needed = lambda filepath: setattr(gui, "docx_init_arg", filepath)

    gui.load_content_into_workspace(
        title="example.docx",
        content="translated content",
        filepath="G:/example.docx",
        clear_progress_cache=True,
    )

    assert gui.docx_init_arg == "G:/example.docx"
    assert gui.cache_cleared is True
