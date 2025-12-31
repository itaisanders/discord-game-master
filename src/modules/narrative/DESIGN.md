# Narrative Module Design

## Overview
The `narrative` module handles the "Protocol Parsing" layer. It interprets raw text output from the AI, executes special instructions (like Dice Rolls), and ensures proper formatting for Discord.

> **Note**: While this module handles formatting, the actual "Smart Chunking" (splitting messages > 2000 chars) is currently implemented directly in the `src/main.py` event loop for simplicity.

## Public Interface

### `parser.py`
The main processor for AI text.

#### Functions
- **`process_response_formatting(text: str) -> Tuple[str, Optional[str], Optional[str]]`**
    - **Description**: The master processing pipeline.
        1.  Filters Away Mentions.
        2.  Renders `DATA_TABLE` blocks to ASCII.
        3.  Extracts `MEMORY_UPDATE` blocks.
        4.  Extracts `VISUAL_PROMPT` blocks.
        5.  Executes `DICE_ROLL` blocks (find-and-replace).
        6.  Intercepts `ROLL_CALL` blocks (queues them).
    - **Returns**: A tuple `(clean_text, memory_facts, visual_prompt)`.

- **`process_dice_rolls(text: str) -> str`**
    - **Description**: Replaces `DICE_ROLL` blocks with the result of `dice.roll()`.

- **`process_roll_calls(text: str) -> str`**
    - **Description**: Extracts `ROLL_CALL` blocks and creates entries in `pending_rolls`.

- **`filter_away_mentions(text: str) -> str`**
    - **Description**: Replaces tags like `<@123>` with `**(Away)**` if the user is in Away Mode.

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
