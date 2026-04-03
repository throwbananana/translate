import pytest

from tests.gui_test_utils import load_gui_module


pytestmark = pytest.mark.unit


def test_workstation_modules_import():
    from ui.workstation import ActionBar, ApiPanel, FilePanel, ProgressPanel

    assert ActionBar is not None
    assert ApiPanel is not None
    assert FilePanel is not None
    assert ProgressPanel is not None


def test_main_gui_references_workstation_modules():
    module = load_gui_module()

    assert module.ActionBar.__module__ == "ui.workstation.action_bar"
    assert module.ApiPanel.__module__ == "ui.workstation.api_panel"
    assert module.FilePanel.__module__ == "ui.workstation.file_panel"
    assert module.ProgressPanel.__module__ == "ui.workstation.progress_panel"
