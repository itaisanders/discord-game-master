# Scripts & Ingestion Design

## Overview
The `scripts/` directory contains utility tools for maintaining the bot, specifically the "Context-Full" ingestion pipeline. This module ensures the AI has access to high-fidelity rulebook data without relying on unreliable RAG vector databases.

## Key Components

### 1. Ingestion Pipeline (`ingest_rpg_book.py`)
*   **Purpose**: Convert PDF rulebooks into clean, context-ready Markdown.
*   **Library**: `pymupdf4llm` (handles OCR, layout preservation, and table extraction).
*   **Input**: `pdf/*.pdf`
*   **Output**: `knowledge/*.md`
*   **Logic**:
    1.  Reads PDF.
    2.  Extracts text with layout awareness (headers, tables).
    3.  (Optional) Uses `rpg_scribe` persona to clean up OCR artifacts (if enabled).
    4.  Writes to `knowledge/`.

### 2. Maintenance Tools
*   **`check_env.py`**: Validates that `.env` exists and has all required keys (`DISCORD_TOKEN`, `GEMINI_API_KEY`).
*   **`analyze_art_style.py`**: (Conceptual) Scans PDFs to generate `.style` files for image generation prompts.

## The `knowledge/` Directory
*   **Role**: **DATA ONLY**.
*   **Content**: Only `.md` files representing ingested books.
*   **Bot Behavior**: On startup, `bot.py` iteratively loads **every** `.md` file in `knowledge/` and appends it to the System Instruction.
*   **Constraint**: Do NOT place `DESIGN.md` or other system docs here, or the bot will think they are RPG rules.
