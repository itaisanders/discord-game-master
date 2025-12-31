# Personas Module Design

## Overview
The `personas/` directory contains the "System Instructions" that define the AI's behavior, tone, and capabilities for specific tasks. Instead of a monolithic prompt, the bot dynamically loads the appropriate persona file based on the context.

## Persona Definitions

### `gm_persona.md`
**Role:** The Dungeon Master / Game Master.
**Responsibilities:**
*   Narrating the story ("Fiction-First").
*   Arbitrating rules (consulting ingested knowledge).
*   Managing spotlight and pacing.
*   Formatting response protocols (`DICE_ROLL`, `VISUAL_PROMPT`).
**Key Instructions:**
*   "Respect the Dice": Never simulate rolls.
*   "Safety First": Respect `/x` stops.

### `memory_architect_persona.md`
**Role:** The Scribe / Historian.
**Responsibilities:**
*   Analyzing the latest narrative beat.
*   Generating succinct `MEMORY_UPDATE` lists.
*   Ensuring facts are recorded in the correct `.ledger`.

### `art_analyzer_persona.md`
**Role:** The Art Director.
**Responsibilities:**
*   Scanning sourcebook PDFs (during ingestion) to extract art style descriptors.
*   Creating `.style` files used to prompt image generation.

### `rpg_scribe_instructions.md`
**Role:** The Transcriber.
**Responsibilities:**
*   Used by `ingest_rpg_book.py` (legacy path) to clean up raw text from PDFs before saving as Markdown.

## Usage
*   **Loading**: `bot.py` reads these files as strings.
*   **Context**: The content is passed to `genai.GenerativeModel(..., system_instruction=USER_PERSONA)`.
