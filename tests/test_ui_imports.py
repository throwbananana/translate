import pytest

from tests.gui_test_utils import load_gui_module


pytestmark = pytest.mark.unit


def test_ui_modules_import():
    from ui.analysis_panel import AnalysisPanel
    from ui.failed_segments_panel import FailedSegmentsPanel
    from ui.glossary_dialog import GlossaryEditorDialog
    from ui.library_panel import LibraryPanel
    from ui.toc_panel import TocPanel

    assert AnalysisPanel is not None
    assert FailedSegmentsPanel is not None
    assert GlossaryEditorDialog is not None
    assert LibraryPanel is not None
    assert TocPanel is not None


def test_main_gui_references_extracted_ui_modules():
    module = load_gui_module()

    assert module.GlossaryEditorDialog.__module__ == "ui.glossary_dialog"
    assert module.FailedSegmentsPanel.__module__ == "ui.failed_segments_panel"
    assert module.AnalysisPanel.__module__ == "ui.analysis_panel"
    assert module.LibraryPanel.__module__ == "ui.library_panel"
    assert module.TocPanel.__module__ == "ui.toc_panel"
