# Memory Module Design

## Overview
The `memory/` directory serves as the persistent database for the campaign. Unlike SQL or NoSQL databases, this project uses **Human-Readable Text Files** (`.ledger`) to ensure that both the AI and the developer can easily read, audit, and edit the game state.

## The Ledger System

### File Format
Ledgers are plain text files, often using pseudo-markdown or list formats.
*   **Extension**: `.ledger`
*   **Location**: `./memory/`

### Core Ledgers

#### `party.ledger`
*   **Purpose**: Tracks character states, stats, and user mapping.
*   **Format**:
    ```text
    [Character: Alistair]
    User: @DiscordUser
    HP: 10/12
    Class: Wizard
    ```

#### `world.ledger` / `locations.ledger`
*   **Purpose**: Tracks facts about the world, visited places, and NPC states.
*   **Format**:
    ```text
    - The Iron Gates are currently locked.
    - NPC logic: The guard captain is suspicious of Alistair.
    ```

#### `inventory.ledger`
*   **Purpose**: Tracks shared party loot.

## Data Flow
1.  **Read**: `bot.py` reads all `.ledger` files at the start of a turn.
2.  **Inject**: Content is appended to the AI's prompt (literally "Here is what you know...").
3.  **Update**: The AI outputs `MEMORY_UPDATE` blocks.
4.  **Write**: The `Memory Architect` (or `bot.py` logic) appends these facts to the files.
