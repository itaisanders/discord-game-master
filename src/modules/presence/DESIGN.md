# Presence Module Design

## Overview
The `presence` module manages player availability states (Away Mode). It persists state to a JSON file to survive bot restarts.

## Public Interface

### `manager.py` > `AwayManager` Class
Manages the `memory/away_status.json` persistence layer.

#### Methods
- **`__init__(filepath: str = "memory/away_status.json")`**
    - Initializes the manager and loads existing data from disk.

- **`set_away(user_id: str, mode: str, last_seen_message_id: int) -> bool`**
    - **Description**: Marks a user as away.
    - **Inputs**:
        - `user_id`: Discord User ID string.
        - `mode`: One of `['auto-pilot', 'off-screen', 'narrative-exit']`.
        - `last_seen_message_id`: ID of the last message seen before going away.
    - **Returns**: `True` if successfully saved, `False` if mode is invalid.

- **`return_user(user_id: str) -> Optional[Dict]`**
    - **Description**: Removes a user from away status (marks them as active).
    - **Returns**: The dictionary containing their previous away data (for summary generation), or `None` if they were not away.

- **`is_away(user_id: str) -> bool`**
    - **Returns**: `True` if the user is in the away database.

- **`get_all_away_users() -> Dict[str, Dict]`**
    - **Returns**: A copy of the entire away status dictionary.

## Data Structures

### Away Status Schema (JSON)
The internal data storage format.
```json
{
  "user_id_string": {
    "mode": "auto-pilot",       // Enum: auto-pilot, off-screen, narrative-exit
    "last_seen_message_id": 123456789,
    "timestamp": 1700000000.0   // Unix timestamp (float)
  }
}
```
