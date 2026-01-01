# Core Module Design

## Overview
The `core` module provides the foundational infrastructure for the application. It handles configuration loading, client initialization (Discord & Gemini), and shared utilities.

## Public Interface

### `config.py`
Exposes environment configuration and validation logic.

#### Functions
- **`validate_config() -> bool`**
    - **Description**: Validates that all required environment variables (`DISCORD_TOKEN`, `GEMINI_API_KEY`, `TARGET_CHANNEL_ID`) are set.
    - **Returns**: `True` if valid, `False` otherwise.

#### Global Variables
- **`DISCORD_TOKEN`** (`str`): The Discord Bot Token.
- **`GEMINI_API_KEY`** (`str`): The Google Gemini API Key.
- **`TARGET_CHANNEL_ID`** (`int`): The integer ID of the main gameplay channel.
- **`PERSONA_FILE`** (`str`): Path to the GM persona file (default: `personas/gm_persona.md`).
- **`AI_MODEL`** (`str`): The specific Gemini model identifier (default: `gemini-2.0-flash-lite`).

### `llm.py`
Abstracts the LLM provider to support modular backends (Gemini, Ollama, etc.).

#### Classes
- **`LLMProvider(ABC)`**: Abstract base class defining the `generate` interface.
- **`GeminiProvider`**: Implementation for Google's Gemini API.
- **`ProviderFactory`**: Factory to instantiate the correct provider based on configuration.

### `views.py`
Contains reusable Discord UI components.

#### Classes

- **`ConfirmView(author: discord.User)`**
    - **Description**: A generic Red/Grey button view for binary confirmation.
    - **Attributes**: `value` (bool) is set to `True` on confirm, `False` on cancel.

- **`FeedbackConfirmView(author, feedback_type, original_message, interpretation, channel, on_confirm_callback)`**
    - **Description**: A specialized Success/Secondary view for confirming AI-interpreted feedback.
    - **Parameters**:
        - `on_confirm_callback`: Async function to execute if the user confirms.

### `client.py`
Initializes and holds singleton client instances.

#### Global Variables
- **`client_genai`** (`google.genai.Client`): The initialized Gemini API client.
- **`client_discord`** (`discord.Client`): The initialized Discord Bot client with `message_content` intents enabled.
- **`tree`** (`discord.app_commands.CommandTree`): The slash command tree attached to `client_discord`.
