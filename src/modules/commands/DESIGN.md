# Commands Module Design

## Overview
The `commands` module handles the user-facing slash commands and their associated static data. It serves as the interaction layer between the Discord user and the bot's internal logic.

## Key Components

### 1. Registry (`registry.py`)
*   **Purpose**: Centralized access to command-related static data.
*   **Functionality**:
    *   `get_help_text()`: Loads and returns the content of `help_text.md`.

### 2. Help Text (`help_text.md`)
*   **Purpose**: Contains the user-facing documentation for all available commands.
*   **Format**: Markdown-formatted text that is displayed in the `/help` command embed.

## Usage
*   **`src/main.py`** imports `get_help_text` from `registry.py` to populate the `/help` command response.
