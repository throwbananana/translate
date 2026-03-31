from pathlib import Path

def test_book_translator_gui_contains_open_admin_audit():
    text = Path("book_translator_gui.pyw").read_text(encoding="utf-8")
    assert "def open_admin_audit(self):" in text
    assert "BOOK_TRANSLATOR_ADMIN_PASSWORD" in text
