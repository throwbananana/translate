import pytest

from config_manager import ConfigManager


pytestmark = pytest.mark.unit

DUMMY_KEY = "unit" + "-gemini"
DUMMY_PW_VALUE = "unit" + "-pw"
DUMMY_ADMIN_VALUE = "unit" + "-admin"


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
    monkeypatch.setenv("GEMINI_API_KEY", DUMMY_KEY)  # pragma: allowlist secret

    manager = ConfigManager(
        config_path=str(tmp_path / "translator_config.json"),
        backup_dir=str(tmp_path / "config_backups"),
    )

    assert manager.get("api_configs.gemini.api_key") == DUMMY_KEY  # pragma: allowlist secret


def test_config_manager_online_search_and_admin_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("ZLIBRARY_EMAIL", "reader@example.com")
    monkeypatch.setenv("ZLIBRARY_PASSWORD", DUMMY_PW_VALUE)  # pragma: allowlist secret
    monkeypatch.setenv("ANNAS_ARCHIVE_DOMAIN", "https://annas-archive.example")
    monkeypatch.setenv("BOOK_TRANSLATOR_ADMIN_PASSWORD", DUMMY_ADMIN_VALUE)  # pragma: allowlist secret

    manager = ConfigManager(
        config_path=str(tmp_path / "translator_config.json"),
        backup_dir=str(tmp_path / "config_backups"),
    )

    assert manager.get("online_search.zlibrary.email") == "reader@example.com"
    assert manager.get("online_search.zlibrary.password") == DUMMY_PW_VALUE  # pragma: allowlist secret
    assert manager.get("online_search.annas_archive.domain") == "https://annas-archive.example"
    assert manager.get_admin_password() == DUMMY_ADMIN_VALUE
