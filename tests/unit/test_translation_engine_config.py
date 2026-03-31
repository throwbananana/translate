import pytest

import translation_engine as te
from translation_engine import create_engine_with_config


pytestmark = pytest.mark.unit


def test_lm_studio_is_available_without_api_key(monkeypatch):
    monkeypatch.setattr(te, "OPENAI_SUPPORT", True)

    engine = create_engine_with_config(
        {
            "api_configs": {
                "lm_studio": {
                    "base_url": "http://127.0.0.1:1234/v1",
                    "model": "local-model",
                    "api_key": "",
                }
            }
        }
    )

    assert "lm_studio" in engine.get_available_providers()
    assert engine.fallback_provider == "lm_studio"


def test_openai_requires_api_key(monkeypatch):
    monkeypatch.setattr(te, "OPENAI_SUPPORT", True)

    engine = create_engine_with_config(
        {
            "api_configs": {
                "openai": {
                    "base_url": "",
                    "model": "gpt-4o-mini",
                    "api_key": "",
                }
            }
        }
    )

    assert "openai" not in engine.get_available_providers()
