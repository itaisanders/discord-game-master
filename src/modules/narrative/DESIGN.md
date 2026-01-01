# Narrative Module Design

## Overview
The `narrative` module handles the "Protocol Parsing" layer. It interprets raw text output from the AI provider, executes special instructions (like Dice Rolls), and ensures proper formatting for Discord.

> **Note**: While this module handles formatting, the actual "Smart Chunking" (splitting messages > 2000 chars) is currently implemented directly in the `src/main.py` event loop for simplicity.

## Public Interface

### `gm_persona.md`
*   **Role/Description**: The "Soul" of the Game Master. Defines the AI's personality, rule arbitration logic, and formatting protocols.
*   **Main Function**: `loader.py` -> `load_system_instruction()` (Injected into main Chat Session).
*   **Supported Protocols**:
    *   `VISUAL_PROMPT`
    *   `MEMORY_UPDATE`
    *   `DICE_ROLL`
    *   `ROLL_CALL`
    *   `DATA_TABLE`
    *   `FEEDBACK_DETECTED`
*   **Flows**: The primary system instruction for the active Game Master chat session.

### `loader.py`
Handles loading the system instruction.

#### Functions
- **`load_system_instruction() -> str`**
    - **Description**: Loads `gm_persona.md` (relative to the module) and injects any `knowledge/*.md` files found in the project root.

### `parser.py`
The main processor for AI text.

#### Functions
- **`process_response_formatting(text: str) -> Tuple[str, Optional[str], Optional[str], List[Dict], Optional[Dict]]`**
    - **Description**: The master processing pipeline.
        1.  Filters Away Mentions.
        2.  Renders `DATA_TABLE` blocks to ASCII.
        3.  Extracts `MEMORY_UPDATE` blocks.
        4.  Extracts `VISUAL_PROMPT` blocks.
        5.  Executes `DICE_ROLL` blocks (find-and-replace).
        6.  Intercepts `ROLL_CALL` blocks (queues them).
        7.  Extracts `FEEDBACK_DETECTED` blocks (implicit feedback).
        8.  Extracts `TABLE_STATE` blocks (implicit table state change).
    - **Returns**: A tuple `(clean_text, memory_facts, visual_prompt, detected_feedback, detected_state_change)`.

- **`process_table_state_detection(text: str) -> Tuple[str, Optional[Dict]]`**
    - **Description**: Extracts `TABLE_STATE` blocks and returns the data (state, reason).

- **`process_feedback_detection(text: str) -> Tuple[str, List[Dict]]`**
    - **Description**: Extracts `FEEDBACK_DETECTED` blocks and returns a list of dictionaries with keys `type`, `user`, and `content`.

- **`process_dice_rolls(text: str) -> str`**
    - **Description**: Replaces `DICE_ROLL` blocks with the result of `dice.roll()`.

- **`process_roll_calls(text: str) -> str`**
    - **Description**: Extracts `ROLL_CALL` blocks and creates entries in `pending_rolls`.

- **`filter_away_mentions(text: str) -> str`**
    - **Description**: Replaces tags like `<@123>` with `**(Away)**` if the user is in Away Mode.

- **`check_length_violation(text: str, limit: int = 1900) -> bool`**
    - **Description**: Checks if the *narrative* portion of the text (excluding protocol blocks like `MEMORY_UPDATE`) exceeds the character limit.

- **`smart_chunk_text(text: str, limit: int = 1900) -> List[str]`**
    - **Description**: Splits text into chunks respecting the limit, prioritizing splitting at paragraph breaks (`\n\n`), then line breaks (`\n`), then sentence endings (`. `). Avoids breaking inside code blocks if possible.

## Data Structures

### `pending_rolls` (Global Dictionary)
Tracks rolls requested by the GM but not yet executed by the player.
```python
pending_rolls = {
    "username_string": {
        "notation": "2d6",
        "reason": "Defy Danger",
        "timestamp": 1700000000.0
    }
}
```

### Protocols
The module interprets standard text protocols defined in `SPECS.md`:
*   `VISUAL_PROMPT`
*   `MEMORY_UPDATE`
*   `DICE_ROLL`
*   `ROLL_CALL`
*   `DATA_TABLE`
*   `FEEDBACK_DETECTED`
