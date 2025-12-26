import os
import json
import time
import pytest
from away import AwayManager

@pytest.fixture
def away_manager(tmp_path):
    """Fixture to create an AwayManager with a temporary file."""
    memory_file = tmp_path / "away_status.json"
    manager = AwayManager(filepath=str(memory_file))
    return manager

def test_set_away(away_manager):
    user_id = "12345"
    mode = "auto-pilot"
    message_id = 99999
    
    success = away_manager.set_away(user_id, mode, message_id)
    
    assert success is True
    assert away_manager.is_away(user_id) is True
    
    data = away_manager.get_away_data(user_id)
    assert data["mode"] == mode
    assert data["last_seen_message_id"] == message_id

def test_return_user(away_manager):
    user_id = "67890"
    away_manager.set_away(user_id, "off-screen", 100)
    
    assert away_manager.is_away(user_id) is True
    
    returned_data = away_manager.return_user(user_id)
    
    assert returned_data is not None
    assert returned_data["mode"] == "off-screen"
    assert away_manager.is_away(user_id) is False

def test_persistence(away_manager, tmp_path):
    user_id = "persistent_user"
    away_manager.set_away(user_id, "narrative-exit", 555)
    
    # Create a new manager instance pointing to the same file
    memory_file = tmp_path / "away_status.json"
    new_manager = AwayManager(filepath=str(memory_file))
    
    assert new_manager.is_away(user_id) is True
    assert new_manager.get_away_data(user_id)["mode"] == "narrative-exit"

def test_invalid_mode(away_manager):
    user_id = "bad_user"
    success = away_manager.set_away(user_id, "invalid-mode", 1)
    assert success is False
    assert away_manager.is_away(user_id) is False

def test_get_all_away_users(away_manager):
    away_manager.set_away("u1", "auto-pilot", 1)
    away_manager.set_away("u2", "off-screen", 2)
    
    all_users = away_manager.get_all_away_users()
    assert len(all_users) == 2
    assert "u1" in all_users
    assert "u2" in all_users
