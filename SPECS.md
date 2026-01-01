# SPECS.md

> **Overview**: Detailed feature specifications, protocol definitions, and domain constraints.

## 1. Protocol Definitions

The bot interacts with the AI via structured Markdown blocks. The AI outputs these blocks, and the bot intercepts/parses them.

### `DICE_ROLL`
Request a true random dice roll.
````markdown
    ```DICE_ROLL
    [Character Name] rolls [notation] for [reason]
    ```
````
*   **Behavior**: Bot replaces block with: `🎲 **[Name]** rolls [notation] for [reason]: [Result]`.

### `ROLL_CALL`
Queue a roll request for a player to execute later.
````markdown
    ```ROLL_CALL
    @PlayerName: [notation] for [reason]
    ```
````
*   **Behavior**: Bot stores request. Player types `/roll` (no args) to execute.

### `MEMORY_UPDATE`
Update the persistent ledger files.
````markdown
    ```MEMORY_UPDATE
    - [Fact 1]
    - [Fact 2]
    ```
````
*   **Behavior**: The `Memory Architect` persona parses these and updates the relevant `.ledger` file.

### `TABLE_STATE`
Request a change in the game's meta-state.
````markdown
    ```TABLE_STATE
    state: [ACTIVE|PAUSED|DEBRIEF|IDLE|SESSION_ZERO]
    reason: [Reason for change]
    ```
````
*   **Behavior**: Bot pauses, does not auto-execute. Presents a "Confirm State Change" button to the chat.

### `VISUAL_PROMPT`
Request an image generation.
````markdown
    ```VISUAL_PROMPT
    [Subject: ...] [Setting: ...] [Lighting: ...] [Style: ...]
    ```
````
*   **Behavior**: Bot triggers `gemini-2.5-flash-image`. Replaces block with generated image embed.

### `DATA_TABLE`
Structure complex data for display.
````markdown
    ```DATA_TABLE
    Title: [Title]
    Header1 | Header2
    Val1    | Val2
    ```
````
*   **Behavior**: Bot renders this as an ASCII table using `prettytable` for Discord compatibility.


## 2. Feature Specifications

### Dice System
*   **Module**: `dice.py`
*   **Notation**: `NdS+M`, `NdSp` (pool), `4dF` (Fate), `d%` (Percentile).
*   **Constraints**: Max 100 dice, Max d1000 face value.
*   **Security**: Must use `secrets` module.

### Away Mode
*   **Module**: `away.py`
*   **Modes**:
    *   `Auto-Pilot`: GM plays character.
    *   `Off-Screen`: Character is passive.
    *   `Narrative Exit`: Character leaves.
*   **Suppression**: Bot removes `@mentions` for away players in AI output.
*   **Catch-Up**: Returning players (`/back`) get a summary of missed messages.

### Knowledge Ingestion (Context-Full)
*   **Input**: PDF Rulebooks in `pdf/`.
*   **Process**: Converted to Markdown via `src/modules/ingestion/ingest_rpg_book.py` using `pymupdf4llm`.
*   **Storage**: `.md` files in `knowledge/`.
*   **Loading**: All files in `knowledge/` are aggregated with the module-specific persona via `src/modules/narrative/loader.py` and injected into the System Instruction at startup.

### Interactive Feedback (`/stars`, `/wishes` & Implicit)
*   **Explicit Flow**:
    1.  User inputs feedback via slash command.
    2.  AI interprets feedback for storing.
    3.  Bot asks User to Confirm/Cancel.
    4.  If Confirmed, written to feedback ledger.
*   **Implicit Flow**:
    1.  AI detects praise ("I loved that!") or desire ("I hope we fight a dragon") in normal chat.
    2.  AI outputs `FEEDBACK_DETECTED` block.
    3.  Bot triggers the confirmation flow for that user.

### Table State Machine
*   **Module**: `src/modules/table/`
*   **States**:
    *   `IDLE`: Bot ignores chat (between sessions).
    *   `SESSION_ZERO`: Active for setup/world-building.
    *   `ACTIVE`: Main game loop.
    *   `PAUSED`: Temporary suspension (bio-breaks).
    *   `DEBRIEF`: Session end (feedback focus).
*   **Persistence**: `memory/table_state.json`.
*   **Logic**: Narrative engine (`on_message`) is gated by state.
    *   `IDLE`, `PAUSED`: No LLM calls.
    *   `ACTIVE`, `SESSION_ZERO`: LLM called with context.
    *   `DEBRIEF`: No LLM calls (except specific feedback triggers).

## 3. Slash Command Registry

The bot implements the following native Discord Slash Commands:

| Command | Arguments | Visibility | Description |
| :--- | :--- | :--- | :--- |
| `/session` | `state` | Public | Manage table state (`start`, `zero`, `pause`, `resume`, `end`, `close`). |
| `/roll` | `[dice]` | Public | Roll dice or execute a pending GM-requested roll. |
| `/help` | None | Ephemeral | Shows the full list of available commands and descriptions. |
| `/sheet` | `[user]` | Ephemeral | Displays a character sheet from the `party.ledger`. |
| `/ledger` | None | Ephemeral | Shows the master campaign ledger (or sends as file). |
| `/away` | `mode` | Public | Set status to `Auto-Pilot`, `Off-Screen`, or `Narrative Exit`. |
| `/back` | None | Public | Return from away; triggers private catch-up summary. |
| `/ooc` | `message` | Public | Send an explicit out-of-character message to the channel. |
| `/visual` | `[prompt]` | Public | Injects a system request for an atmospheric image. |
| `/rewind` | `direction` | Public | Undoes the last GM narrative and suggests a new path. |
| `/x` | `[reason]` | Public | Safety tool; stops scene, rewinds facts, and pivots. |
| `/stars` | `message` | Ephemeral | Record something you enjoyed (requires confirmation). |
| `/wishes` | `message` | Ephemeral | Record something you want to see (requires confirmation). |
| `/reset_memory` | None | Ephemeral | **Admin Only**: Wipes all ledgers and rebuilds from history. |

## 4. Domain Constraints

### Discord
*   **Message Limit**: 2000 chars. Bot uses `smart_chunk` to split long messages ~1900 chars without breaking Markdown.
*   **Formatting**: No native tables (use ASCII). No headings (use Bold).

### RPG Logic
*   **Fiction-First**: Narrative takes precedence.
*   **Safety**: `/x` command immediately stops generation, rewinds memory, and pivots narrative.

### Feature Constraints
*   **Bard Module**: Slash commands (`/summary`, `/voice`) are **disabled** if no voices are configured in the Voice Registry.

