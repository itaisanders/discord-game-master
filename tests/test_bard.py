import pytest
import os
import json
from src.modules.bard.manager import BardManager
from src.modules.bard.voices import VOICE_REGISTRY

@pytest.fixture
def temp_settings_file(tmp_path):
    d = tmp_path / "memory"
    d.mkdir()
    f = d / "bard_settings.json"
    return str(f)

def test_bard_manager_init(temp_settings_file):
    manager = BardManager(settings_file=temp_settings_file)
    assert manager.is_configured() == (len(VOICE_REGISTRY) > 0)
    assert manager.selected_voice_key in VOICE_REGISTRY

def test_bard_manager_set_voice(temp_settings_file):
    manager = BardManager(settings_file=temp_settings_file)
    keys = list(VOICE_REGISTRY.keys())
    if len(keys) > 1:
        target = keys[1]
        assert manager.set_selected_voice(target)
        assert manager.selected_voice_key == target
        
        # Test persistence
        new_manager = BardManager(settings_file=temp_settings_file)
        assert new_manager.selected_voice_key == target

def test_bard_manager_invalid_voice(temp_settings_file):
    manager = BardManager(settings_file=temp_settings_file)
    assert not manager.set_selected_voice("non_existent_voice")

def test_is_configured_empty_registry(temp_settings_file, monkeypatch):
    monkeypatch.setattr("src.modules.bard.manager.VOICE_REGISTRY", {})
    manager = BardManager(settings_file=temp_settings_file)
    assert not manager.is_configured()
