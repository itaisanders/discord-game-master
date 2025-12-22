
import pytest
import re
from bot import process_response_formatting, render_table_as_ascii

def test_process_response_formatting_data_table():
    """Test that DATA_TABLE blocks are correctly identified and processed."""
    sample_text = """
Hello world.
```DATA_TABLE
Title: Test Table
Header 1 | Header 2
Val 1 | Val 2
```
Lore text.
"""
    cleaned_text, facts, visual_prompt = process_response_formatting(sample_text)
    
    assert "**Test Table**" in cleaned_text
    assert "Val 1" in cleaned_text
    assert "Val 2" in cleaned_text
    assert "```text" in cleaned_text
    assert facts is None
    assert visual_prompt is None

def test_process_response_formatting_memory_update():
    """Test that MEMORY_UPDATE blocks are correctly extracted and stripped."""
    sample_text = """
Victory!
```MEMORY_UPDATE
- Fact A
- Fact B
```
Next scene.
"""
    cleaned_text, facts, visual_prompt = process_response_formatting(sample_text)
    
    assert "Victory!" in cleaned_text
    assert "Next scene." in cleaned_text
    assert "Fact A" in facts
    assert "Fact B" in facts
    assert "MEMORY_UPDATE" not in cleaned_text

def test_process_response_formatting_visual_prompt():
    """Test that VISUAL_PROMPT blocks are correctly extracted and stripped."""
    sample_text = """
The scene is set.
```VISUAL_PROMPT
A dark tower in the rain.
```
"""
    cleaned_text, facts, visual_prompt = process_response_formatting(sample_text)
    
    assert "The scene is set." in cleaned_text
    assert visual_prompt == "A dark tower in the rain."
    assert "VISUAL_PROMPT" not in cleaned_text

def test_process_response_formatting_combined():
    """Test multiple protocols in one response."""
    sample_text = """
Heroic action!
```DATA_TABLE
Title: Stats
Stat | Value
HP | 10
```
```MEMORY_UPDATE
- HP changed to 10
```
```VISUAL_PROMPT
Portrait of a hero
```
"""
    cleaned_text, facts, visual_prompt = process_response_formatting(sample_text)
    
    assert "**Stats**" in cleaned_text
    assert "HP change" in facts
    assert visual_prompt == "Portrait of a hero"
    assert "MEMORY_UPDATE" not in cleaned_text
    assert "VISUAL_PROMPT" not in cleaned_text

def test_render_table_as_ascii_malformed():
    """Test error handling for malformed tables."""
    # We mock the match object
    class MockMatch:
        def __init__(self, content):
            self.content = content
        def group(self, n):
            return self.content
            
    bad_table = "Just random text without pipes"
    match = MockMatch(bad_table)
    result = render_table_as_ascii(match)
    
    # It should return the original if it fails headers or just produce a table with no rows?
    # Our logic says 'if headers:' so if no pipes, it returns match.group(0)
    assert result == bad_table
