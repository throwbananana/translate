import pytest

from config_manager import ConfigManager


pytestmark = pytest.mark.unit


def test_config_manager_uses_temp_paths(tmp_path):
    config_path = tmp_path / "translator_config.json"
    backup_dir = tmp_path / "config_backups"

    manager = ConfigManager(config_path=str(config_path), backup_dir=str(backup_dir))

    manager.set("target_language", "English", save=False)
    assert manager.get("target_language") == "English"

    saved = manager.save(create_backup=False)
    assert saved is True
    assert config_path.exists()
    assert backup_dir.exists()


def test_config_manager_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "env-gemini-key")

    manager = ConfigManager(
        config_path=str(tmp_path / "translator_config.json"),
        backup_dir=str(tmp_path / "config_backups"),
    )

    assert manager.get("api_configs.gemini.api_key") == "env-gemini-key"


def test_config_manager_online_search_and_admin_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("ZLIBRARY_EMAIL", "reader@example.com")
    monkeypatch.setenv("ZLIBRARY_PASSWORD", "top-secret")
    monkeypatch.setenv("ANNAS_ARCHIVE_DOMAIN", "https://annas-archive.example")
    monkeypatch.setenv("BOOK_TRANSLATOR_ADMIN_PASSWORD", "super-admin")

    manager = ConfigManager(
        config_path=str(tmp_path / "translator_config.json"),
        backup_dir=str(tmp_path / "config_backups"),
    )

    assert manager.get("online_search.zlibrary.email") == "reader@example.com"
    assert manager.get("online_search.zlibrary.password") == "top-secret"
    assert manager.get("online_search.annas_archive.domain") == "https://annas-archive.example"
    assert manager.get_admin_password() == "super-admin"
