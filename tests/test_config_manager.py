from pathlib import Path

from config_manager import ConfigManager


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
