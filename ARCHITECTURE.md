# ARCHITECTURE.md

> **Overview**: High-level design, core patterns, and technology stack.

## 1. System Overview

**Discord RPG Game Master Bot** is an advanced AI-powered application designed to facilitate immersive, "Fiction-First" tabletop RPG sessions. It operates as a bridge between Discord's event-driven interface and Google's Gemini generative AI, managing game state, narrative flow, and mechanical integrity.

### Core Purpose
*   **Immersive Narration**: Facilitate text-based RPGs with high-quality AI storytelling.
*   **State Management**: Maintain persistent campaign context (characters, logic, world) across sessions.
*   **Rule Arbitration**: Provide intelligent rule lookups via ingested sourcebooks.
*   **Mechanical Integrity**: Ensure fair play through cryptographically secure, non-AI dice rolling.

### Technology Stack
*   **Language**: Python 3.10+
*   **Interface**: `discord.py` (Async/Slash Commands)
*   **AI Backend**: `google-genai`
    *   Text: `gemini-2.0-flash-lite`
    *   Images: `gemini-2.5-flash-image`
*   **Persistence**: Flat-file system (`.ledger` files) for human-readable, reliable state.
*   **Knowledge Base**: Markdown-based RAG (Direct Ingestion).

---

## 2. Core Architectural Decisions

### Async-First Event Loop
The bot utilizes an asynchronous architecture to prevent blocking Discord's heartbeat. All I/O operations—specifically Gemini API calls—**must** use `client_genai.aio`. Synchronous blocking calls are strictly prohibited as they lead to connection timeouts (`Heartbeat blocked`).

### Native Slash Command Interface
User interaction is exclusively driven by **Discord Slash Commands** (`/roll`, `/rewind`, `/sheet`).
*   **Benefits**: Typesafety, auto-completion, and discoverability.
*   **Separation**: The `on_message` event handler is reserved for narrative flow and in-character text, not command parsing.

### System Event Injection
A primary pattern for complex interactions. Instead of code directly manipulating the narrative, the bot **injects** structured system events into the AI's chat context.
*   **Example**: `/visual "dark alley"` -> Injects `[System Event: Player requested visual...]`.
*   **Outcome**: The AI interprets the request within the fiction and generates the appropriate Protocol Block response, ensuring narrative consistency.

### Encapsulated Multi-Persona Architecture
The bot avoids a single monolithic system instruction. Instead, it utilizes a **Modular Persona** system where each feature module owns its own system instructions. This ensures strong encapsulation and allows for specialized AI behaviors:
*   **Game Master (`src/modules/narrative/gm_persona.md`)**: The primary narrator and rule arbiter.
*   **Memory Architect (`src/modules/memory/architect_persona.md`)**: Specialized in summarizing events and updating `.ledger` files.
*   **Art Analyzer (`src/modules/ingestion/art_analyzer_persona.md`)**: Extracts style guidelines from rulebooks.

Each module is responsible for loading its own persona files using relative paths, removing reliance on global configuration files for internal AI logic.

### Persistent Memory System (The Ledger)
State is not stored in a database but in **human-readable `.ledger` text files**.
*   **Source of Truth**: `party.ledger`, `world.ledger`, etc.
*   **Updates**: The AI outputs `MEMORY_UPDATE` blocks; the bot parses them and appends/modifies the files.
*   **Retrieval**: Ledgers are read and injected into the AI's system instruction, giving it "memory" of past events.

### Dice Integrity ("Respect the Dice")
Randomness is fully decoupled from the AI.
*   **Mechanism**: The `dice.py` module uses Python's `secrets` library.
*   **Flow**: AI requests a roll (via `DICE_ROLL` protocol) -> Bot intercepts -> Bot calculates result -> Bot injects result back into chat.
*   **Principle**: The AI describes the *outcome* of the roll, but never determines the *number*.

---

## 3. Data Flow & State Management

### The "Document-Act" Loop
The system operates on a cyclical flow:
1.  **Input**: User sends message or command.
2.  **Context Assembly**: Bot gathers current ledgers, relevant knowledge chunks, and chat history.
3.  **Processing**:
    *   *Commands*: Python logic handles state (e.g., `away.py`).
    *   *Narrative*: Gemini generates response.
4.  **Protocol Interception**: Bot scans AI output for blocks (`DICE_ROLL`, `MEMORY_UPDATE`).
5.  **Action**:
    *   Dice are rolled.
    *   Ledgers are updated.
    *   Images are generated.
6.  **Output**: Final formatted message sent to Discord.

### Directory Structure
*   `src/`: Application source code.
    *   `src/main.py`: Entry point and command orchestration.
    *   `src/core/`: Application infrastructure (Config, Clients).
    *   `src/modules/`: Feature logic.
        *   `src/modules/dice/`: RNG and rolling logic.
        *   `src/modules/presence/`: Away mode state machine.
        *   `src/modules/memory/`: Ledger I/O, interaction logic, and the **Memory Architect** persona.
        *   `src/modules/narrative/`: AI parsing, Protocol handling, and the **GM** persona.
        *   `src/modules/commands/`: Slash command registry and help documentation.
        *   `src/modules/ingestion/`: Tools for rulebook ingestion and art style analysis.
*   `knowledge/`: Ingested rulebooks (.md).
*   `memory/`: Campaign state (.ledger).
*   `scripts/`: Maintenance and utility scripts.
