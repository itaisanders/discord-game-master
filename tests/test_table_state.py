import pytest
import os
import json
from src.modules.table.state import TableManager, TableState

@pytest.fixture
def temp_state_file(tmp_path):
    d = tmp_path / "memory"
    d.mkdir()
    f = d / "table_state.json"
    return str(f)

def test_initial_state(temp_state_file):
    manager = TableManager(state_file=temp_state_file)
    assert manager.get_state() == TableState.IDLE
    assert not manager.is_narrative_active()

def test_set_state(temp_state_file):
    manager = TableManager(state_file=temp_state_file)
    manager.set_state(TableState.ACTIVE)
    assert manager.get_state() == TableState.ACTIVE
    assert manager.is_narrative_active()

def test_persistence(temp_state_file):
    manager = TableManager(state_file=temp_state_file)
    manager.set_state(TableState.SESSION_ZERO)
    
    # New manager instance should load previous state
    new_manager = TableManager(state_file=temp_state_file)
    assert new_manager.get_state() == TableState.SESSION_ZERO
    assert new_manager.is_narrative_active()

def test_is_narrative_active(temp_state_file):
    manager = TableManager(state_file=temp_state_file)
    
    manager.set_state(TableState.IDLE)
    assert not manager.is_narrative_active()
    
    manager.set_state(TableState.SESSION_ZERO)
    assert manager.is_narrative_active()
    
    manager.set_state(TableState.ACTIVE)
    assert manager.is_narrative_active()
    
    manager.set_state(TableState.PAUSED)
    assert not manager.is_narrative_active()
    
    manager.set_state(TableState.DEBRIEF)
    assert not manager.is_narrative_active()

def test_is_paused(temp_state_file):
    manager = TableManager(state_file=temp_state_file)
    manager.set_state(TableState.PAUSED)
    assert manager.is_paused()
    manager.set_state(TableState.ACTIVE)
    assert not manager.is_paused()
