# GEMINI.md: Project Overview & Development Guide

This document provides a comprehensive overview of the **Discord RPG Game Master Bot** project, its architecture, and development conventions, intended for use as an instructional context.

## 1. Project Overview

This is a sophisticated, AI-powered Discord bot designed to act as a Game Master for text-based tabletop RPGs. It uses the Google Gemini API for narrative generation (`gemini-2.0-flash-lite`) and atmospheric image creation (`gemini-2.5-flash-image`).

The project is well-structured, with a clear separation of concerns, and employs advanced techniques to create an immersive and robust gameplay experience:

*   **Core Technology**: Python 3.10+, `discord.py`, and `google-genai`.
*   **Architecture**: An async-first, event-driven design centered around native Discord Slash Commands.
*   **Retrieval-Augmented Generation (RAG)**: The bot gains knowledge of specific game rules by loading Markdown (`.md`) files from the `./knowledge` directory directly into the AI's system context on startup.
*   **Persistent Memory**: Campaign state (character sheets, world facts, NPC details) is maintained across sessions in human-readable `.ledger` files within the `./memory` directory. A dedicated "Memory Architect" persona handles updates.
*   **Multi-Persona System**: The bot uses different "persona" files (located in `./personas`) as system instructions to guide the AI's behavior for specific tasks, such as game mastering, memory management, or character sheet extraction.
*   **Protocol-Driven Interaction**: The AI's responses are structured with special blocks (e.g., `DICE_ROLL`, `MEMORY_UPDATE`, `VISUAL_PROMPT`) that the bot's code intercepts to trigger actions, ensuring reliability and separating AI narration from game mechanics.
*   **Dice Integrity**: A core principle is "Respect the Dice." All dice rolls are executed by a `dice.py` module that uses Python's cryptographically secure `secrets` library, never by AI simulation.
*   **Multiplayer Focus**: Features like an "Away Mode" (`away.py`) for absent players and a `[SIGNAL: SILENCE]` protocol to prevent the AI from interrupting player-to-player roleplaying demonstrate a deep focus on a smooth multiplayer experience.

The architectural principles and development patterns are meticulously documented in `AGENTS.md`, which serves as the "Architectural Source of Truth" for the project.

## 2. Building and Running

### Setup

1.  **Install Dependencies**: Ensure Python 3.10+ is installed. Then, install the required packages.

    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment**: Copy the example environment file and fill in your API keys and Discord channel ID.

    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

    **Required `.env` variables**:
    *   `DISCORD_TOKEN`: Your Discord bot token.
    *   `GEMINI_API_KEY`: Your Google Gemini API key.
    *   `TARGET_CHANNEL_ID`: The ID of the Discord channel the bot should operate in.

### Running the Bot

The project includes a management script for running the bot as a persistent background process.

*   **Start the bot**:
    ```bash
    ./manage.sh start
    ```
*   **Stop the bot**:
    ```bash
    ./manage.sh stop
    ```
*   **Check status**:
    ```bash
    ./manage.sh status
    ```
*   **View logs**:
    ```bash
    ./manage.sh log
    ```

For local development and testing, you can run the bot directly in the foreground or in a special terminal-only mode.

*   **Run live on Discord (foreground)**:
    ```bash
    python3 bot.py
    ```
*   **Run in terminal mode (for testing GM logic without Discord)**:
    ```bash
    python3 bot.py --terminal
    ```

### Testing the Project

The project uses `pytest` for automated testing.

*   **Run all tests**:
    ```bash
    pytest
    ```
*   **Run a specific test file**:
    ```bash
    pytest tests/test_bot_logic.py
    ```

## 3. Development Conventions

*   **Async-First**: All I/O operations, especially calls to the Gemini API, **must** use asynchronous libraries (`client_genai.aio`) to avoid blocking the Discord client's event loop.
*   **System Instructions as Code**: The primary logic for the AI's behavior is defined in the `.md` files within the `personas/` directory. To change the GM's behavior, start by editing `personas/gm_persona.md`.
*   **Protocol Blocks**: When adding features that require structured data exchange with the AI, follow the established pattern of using protocol blocks (e.g., ```` ```MY_PROTOCOL ... ``` ````) and add a corresponding parser to the `process_response_formatting` function in `bot.py`.
*   **Slash Commands**: All new player-facing commands should be implemented as native Discord Slash Commands using the `@tree.command()` decorator in `bot.py`.
*   **Stateful Management**: For complex features like player absence, encapsulate the logic and state management into a dedicated class or module (see `away.py` as an example).
*   **Testing**: New features, especially those involving protocol parsing or state changes, should be accompanied by unit tests in the `tests/` directory.

### Development Workflow

A crucial part of our development process is ensuring stability and correctness. Whenever code changes are made:

1.  **Run All Tests**: Execute the full test suite using `pytest`.
    ```bash
    pytest
    ```
2.  **Verify Pass**: Confirm that all tests pass successfully.
3.  **Restart Bot**: Only if all tests pass, restart the bot to apply the changes.
    ```bash
    ./manage.sh restart
    ```

4.  **Git Commits**: When committing changes, explicitly add only the relevant source code, test, and documentation files (`.py`, `.md`, `.ini`, etc.). **Do not stage or commit the `tasks.md` file.**
