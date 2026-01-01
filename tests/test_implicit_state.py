import pytest
from src.modules.narrative.parser import process_table_state_detection, process_response_formatting

def test_extract_table_state_simple():
    text = """
    We have reached the end of the chapter.
    ```TABLE_STATE
    state: DEBRIEF
    reason: Cliffhanger achieved.
    ```
    """
    clean_text, detected = process_table_state_detection(text)
    
    assert "DEBRIEF" in detected['state']
    assert "Cliffhanger achieved." in detected['reason']
    assert "```TABLE_STATE" not in clean_text
    assert "We have reached the end of the chapter." in clean_text.strip()

def test_extract_table_state_case_insensitive():
    text = """
    ```table_state
    State: Paused
    REASON: Bio break
    ```
    """
    clean_text, detected = process_table_state_detection(text)
    
    assert detected['state'].lower() == "paused"
    assert detected['reason'].lower() == "bio break"

def test_full_pipeline_integration():
    text = """
    The dragon falls!
    ```MEMORY_UPDATE
    - Dragon is dead
    ```
    ```TABLE_STATE
    state: DEBRIEF
    reason: Boss defeated
    ```
    """
    final_text, facts, visual, feedback, state_change = process_response_formatting(text)
    
    assert "The dragon falls!" in final_text
    assert "Dragon is dead" in facts
    assert state_change['state'] == "DEBRIEF"
