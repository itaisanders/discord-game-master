# Memory Module Design

## Overview
The `memory` module handles reading and updating the campaign's persistent state files (`.ledger`) and the Multi-Persona system. It bridges the gap between raw text files and the AI's context.

## Public Interface

### `service.py`
Stateless functions for file I/O and AI interactions regarding memory.

#### Context Loading
- **`load_full_context() -> str`**
    - **Description**: Aggregates the `PERSONA_FILE` and all `.md` files in `knowledge/`.
    - **Returns**: A single compiled string containing the System Instruction.

- **`load_memory() -> str`**
    - **Description**: Reads all `*.ledger` files in `memory/`.
    - **Returns**: A string block formatted with `--- CAMPAIGN LEDGER: name ---` headers.

#### Ledger Manipulation
- **`save_ledger_files(response_text: str) -> int`**
    - **Description**: Parses `FILE:` or ```FILE: ...``` blocks from an AI response string and writes them to the `memory/` directory.
    - **Returns**: Number of files saved.

- **`update_ledgers_logic(update_facts: str) -> Coroutine`**
    - **Description**: Asynchronous. Calls the "Memory Architect" persona to integrate `update_facts` into the physical ledger files.

- **`reverse_ledgers_logic(facts_to_reverse: str) -> Coroutine`**
    - **Description**: Asynchronous. Calls the "Memory Architect" to remove or reverse specific facts.

#### Feedback System
- **`get_feedback_interpretation(feedback_type: str, message: str) -> str`**
    - **Description**: Uses GM Persona to interpret user feedback (`star`/`wish`) into a structured `FEEDBACK_UPDATE` block.
    
- **`record_feedback(feedback_type: str, user: str, message: str, interpretation: str) -> void`**
    - **Description**: Parses `FEEDBACK_UPDATE` and appends it to `memory/feedback.ledger`.

#### Data Access
- **`get_character_name(user_id: str, user_name: str) -> Optional[str]`**
    - **Description**: Scans `party.ledger` (pipe-delimited table) to find the Character Name associated with a Discord ID or Username.
    - **Returns**: Character Name string or `None`.

- **`fetch_character_sheet(character_name: str) -> Optional[str]`**
    - **Description**: Extracts the `character_sheet` code block for a specific character from `party.ledger`.
    - **Returns**: The content of the sheet or `None`.

## Data Structures

### Filesystem Conventions
- **`memory/*.ledger`**: Text files storing campaign state.
    - **`party.ledger`**: Must contain a Markdown table mapping `Name | Class | User`.
    - **`world.ledger`**: General world state.
    - **`feedback.ledger`**: Stores player feedback (Stars & Wishes).
- **`knowledge/*.md`**: Static rules/lore injected into System Instruction.
