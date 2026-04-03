import pytest

from tests.gui_test_utils import load_gui_module


pytestmark = pytest.mark.unit


def test_content_notebook_module_import():
    from ui.content_notebook import ContentNotebook

    assert ContentNotebook is not None


def test_main_gui_references_content_notebook_module():
    module = load_gui_module()

    assert module.ContentNotebook.__module__ == "ui.content_notebook"
