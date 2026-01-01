
import pytest
import pathlib
import os
from unittest.mock import MagicMock, patch, AsyncMock
from src.modules.memory.service import save_ledger_files, update_ledgers_logic

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
    with patch("src.modules.memory.service.pathlib.Path") as mock_path_class:
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

@pytest.mark.asyncio
@patch("src.modules.memory.service.llm_provider.generate", new_callable=AsyncMock)
@patch("src.modules.memory.service.load_memory")
@patch("src.modules.memory.service.save_ledger_files")
async def test_update_ledgers_logic(mock_save, mock_load, mock_gen, temp_memory_dir):
    """Test the coordination of update_ledgers_logic."""
    mock_load.return_value = "Existing content"
    
    # Mock Response
    mock_gen.return_value = "FILE: update.ledger\nNew content"
    
    # We need to make sure the persona exists for the test
    with patch("src.modules.memory.service.pathlib.Path") as mock_path_class:
        # Create a mock for the persona file path
        mock_persona_path = MagicMock()
        mock_persona_path.exists.return_value = True
        mock_persona_path.read_text.return_value = "Persona content"
        
        # Configure Path(__file__).parent / "architect_persona.md"
        # Path() returns mock_path_instance
        # mock_path_instance.parent returns mock_parent
        # mock_parent / "architect_persona.md" returns mock_persona_path
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_path_instance.parent.__truediv__.return_value = mock_persona_path
        
        await update_ledgers_logic("Fact to add")
    
    mock_gen.assert_called_once()
    mock_save.assert_called_once_with("FILE: update.ledger\nNew content")

def test_save_ledger_files_extension_handling(temp_memory_dir):
    """Ensure .ledger extension is added if missing."""
    with patch("src.modules.memory.service.pathlib.Path") as mock_path_class:
        mock_dir = MagicMock()
        mock_path_class.return_value = mock_dir
        mock_file = MagicMock()
        mock_dir.__truediv__.return_value = mock_file
        
        sample = "```FILE: auto\nContent```"
        save_ledger_files(sample)
        
        # Check if it was called with 'auto.ledger'
        # mock_dir / 'auto.ledger'
        mock_dir.__truediv__.assert_called_with("auto.ledger")
