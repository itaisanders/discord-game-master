# Main Application Design (`src/main.py`)

## Overview
`src/main.py` is the application entry point and event orchestrator. It ties together the modular components (`core`, `dice`, `presence`, `memory`, `narrative`), initializes the Discord/AI provider clients, and registers all user-facing interactions.

## Architecture Role
- **Event Loop**: Manages the `on_ready` and `on_message` Discord events.
- **Protocol Router**: Dispatches non-command interactions (narrative text) to the AI provider and handles the resulting protocols (`DICE_ROLL`, `MEMORY_UPDATE`, etc.).
- **Command Registry**: Defines and registers all Slash Commands via the `discord.app_commands.CommandTree`.

## Public Interface (Slash Commands)

The following commands are registered on the `tree` object and synced to Discord:

| Command | Arguments | Visibility | Function Description |
| :--- | :--- | :--- | :--- |
| **`/roll`** | `dice` (Optional) | Public | Executes `dice.rolling.roll()`. If no arg, checks `pending_rolls` queue. |
| **`/sheet`** | `user` (Optional) | Ephemeral | calls `memory.service.fetch_character_sheet()` to display stats. |
| **`/ledger`** | None | Ephemeral | calls `memory.service.load_memory()` to show campaign state. |
| **`/help`** | None | Ephemeral | Loads and displays `personas/help_text.md`. |
| **`/away`** | `mode` (Choice) | Public | Calls `presence.manager.AwayManager.set_away()`. |
| **`/back`** | None | Public | Calls `presence.manager.AwayManager.return_user()`. |
| **`/ooc`** | `message` | Public | Sends stylized `[OOC]` message to channel. |
| **`/visual`** | `prompt` (Optional)| Public | Injects a `[System Event: Visual Prompt...]` to trigger AI art. |
| **`/rewind`** | `direction` | Public | Reverses last ledger update and injects `[System Event: Rewind...]`. |
| **`/x`** | `reason` (Optional) | Public | Safety pivot. Reverses last update and injects `[System Event: X-Card...]`. |
| **`/stars`** | `message` | Ephemeral | Feedback system. Uses `get_feedback_interpretation` + `FeedbackConfirmView`. |
| **`/wishes`** | `message` | Ephemeral | Feedback system. Uses `get_feedback_interpretation` + `FeedbackConfirmView`. |
| **`/reset_memory`**| None | Ephemeral | **Admin**. Wipes ledgers and rebuilds via `memory_architect_persona.md`. |

## Terminal Mode
- **`run_terminal_mode()`**: A standalone loop for testing the GM persona and AI logic without Discord. It mocks the history structure and prints responses to `stdout`.
