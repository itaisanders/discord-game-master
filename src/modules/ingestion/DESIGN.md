# Ingestion Module Design

## Overview
The `ingestion` module handles the pipeline for converting raw high-fidelity rulebooks (PDFs) into AI-ready Markdown context ("Context-Full" Knowledge). This module ensures the AI has access to high-fidelity rulebook data without relying on unreliable RAG vector databases.

## Key Components

### 1. Ingestion Pipeline (`ingest_rpg_book.py`)
*   **Purpose**: Convert PDF rulebooks into clean, context-ready Markdown.
*   **Library**: `pymupdf4llm` (handles OCR, layout preservation, and table extraction).
*   **Input**: `pdf/*.pdf`
*   **Output**: `knowledge/*.md`
*   **Logic**:
    1.  Reads PDF.
    2.  Extracts text with layout awareness (headers, tables).
    3.  Writes to `knowledge/`.

### 2. Art Style Analyzer (`analyze_art_style.py`)
*   **Purpose**: Scans PDFs to generate textual styleguides used for creating atmospheric visuals.
*   **Input**: `pdf/*.pdf` or `active upload`
*   **Output**: `knowledge/*.style` (text file)
*   **Persona**: Uses `art_analyzer_persona.md` (relative to the module) to interpret visual elements.

## Data Structures
*   **`knowledge/*.md`**: The final output format.
*   **`knowledge/*.style`**: Auxiliary style definitions.

## The `knowledge/` Directory
*   **Role**: **DATA ONLY**.
*   **Content**: Only `.md` files representing ingested books.
*   **Bot Behavior**: On startup, `src/main.py` iteratively loads **every** `.md` file in `knowledge/` and appends it to the System Instruction.
*   **Constraint**: Do NOT place `DESIGN.md` or other system docs here, or the bot will think they are RPG rules.
