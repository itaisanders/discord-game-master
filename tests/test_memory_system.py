
import pytest
import pathlib
import os
from unittest.mock import MagicMock, patch
from bot import save_ledger_files, update_ledgers_logic

@pytest.fixture
def temp_memory_dir(tmp_path):
    """Sets override for memory directory using patch."""
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir()
    return mem_dir

def test_save_ledger_files(temp_memory_dir):
    """Test parsing and saving FILE: blocks."""
    sample_response = """
```FILE: party.ledger
Title: Party
Name | HP
Hero | 10
```
```FILE: world.ledger
Fact 1
Fact 2
```
"""
    with patch("bot.pathlib.Path") as mock_path_class:
         # Mocking Path("./memory") / filename
         mock_dir = MagicMock()
         mock_path_class.return_value = mock_dir
         
         mock_file = MagicMock()
         mock_dir.__truediv__.return_value = mock_file
         
         count = save_ledger_files(sample_response)
         
         assert count == 2
         # Verify that mkdir and write_text were called
         assert mock_file.parent.mkdir.called
         assert mock_file.write_text.called

@patch("bot.client_genai.models.generate_content")
@patch("bot.load_memory")
@patch("bot.save_ledger_files")
def test_update_ledgers_logic(mock_save, mock_load, mock_gen, temp_memory_dir):
    """Test the coordination of update_ledgers_logic."""
    mock_load.return_value = "Existing content"
    
    # Mock Response
    mock_res = MagicMock()
    mock_res.text = "FILE: update.ledger\nNew content"
    mock_gen.return_value = mock_res
    
    # We need to make sure the persona exists for the test
    with patch("bot.pathlib.Path") as mock_path:
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.read_text.return_value = "Persona content"
        update_ledgers_logic("Fact to add")
    
    mock_gen.assert_called_once()
    mock_save.assert_called_once_with("FILE: update.ledger\nNew content")

def test_save_ledger_files_extension_handling(temp_memory_dir):
    """Ensure .ledger extension is added if missing."""
    with patch("bot.pathlib.Path") as mock_path_class:
        mock_dir = MagicMock()
        mock_path_class.return_value = mock_dir
        mock_file = MagicMock()
        mock_dir.__truediv__.return_value = mock_file
        
        sample = "```FILE: auto\nContent```"
        save_ledger_files(sample)
        
        # Check if it was called with 'auto.ledger'
        # mock_dir / 'auto.ledger'
        mock_dir.__truediv__.assert_called_with("auto.ledger")
