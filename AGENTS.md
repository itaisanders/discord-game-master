# AGENTS.md - Architectural Source of Truth

> **Last Updated**: 2025-12-26  
> **For**: Future AI agents working on this codebase

---

## 1. Project DNA

### Identity
**Discord RPG Game Master Bot** - An advanced Discord bot that serves as an AI-powered Game Master for text-based multiplayer tabletop RPGs.

### Core Purpose
- Facilitate immersive, "Fiction-First" tabletop RPG sessions in Discord
- Manage multiplayer party context across long-running campaigns
- Provide intelligent rule lookups via RAG-indexed PDF sourcebooks
- Generate atmospheric artwork using AI image generation
- Maintain persistent campaign memory across bot restarts

### Technology Foundation
- **Language**: Python 3.10+
- **Platform**: Discord (async event-driven architecture)
- **AI Provider**: Google Gemini API
  - `gemini-2.0-flash-lite` for text generation (GM narration)
  - `gemini-2.5-flash-image` for visual generation
- **Knowledge Base**: RAG (Retrieval-Augmented Generation) with File Search

---

## 2. Established Patterns

### Architectural Decisions

#### Async-First Design
**All Gemini API calls MUST use `client_genai.aio`** to prevent blocking the Discord event loop:
```python
# ✅ Correct
response = await client_genai.aio.models.generate_content(...)
chat = client_genai.aio.chats.create(...)

# ❌ Incorrect (blocks heartbeat)
response = client_genai.models.generate_content(...)
```

**Rationale**: Synchronous calls caused "heartbeat blocked for more than 10 seconds" warnings, leading to connection drops.

#### Multi-Persona Architecture
The bot uses **specialized AI personas** for different tasks:
- `gm_persona.md` - Core Game Master behavior and rules
- `memory_architect_persona.md` - Manages `.ledger` file updates
- `art_analyzer_persona.md` - Extracts art style from sourcebooks
- `rpg_scribe_instructions.md` - PDF-to-Markdown transcription

**Pattern**: Load persona files as `system_instruction` for targeted behavior.

#### Protocol-Based Parsing
The bot uses **regex-based protocol blocks** for structured data:
```markdown
| ```DATA_TABLE
| Title: Party Status
| Name | HP | Stress
| Alistair | 12/15 | 3/10
| ```

| ```MEMORY_UPDATE
| - Alistair took 3 damage
| - Party entered the Iron District
| ```

| ```VISUAL_PROMPT
| [Subject: ...] [Setting: ...] [Lighting: ...] [Style: ...]
| ```
```

**Implementation**: `process_response_formatting()` in `bot.py` uses case-insensitive regex with fallback patterns.

#### Persistent Memory System
- **Storage**: File-based `.ledger` files in `memory/` directory
- **Management**: Memory Architect persona processes `MEMORY_UPDATE` blocks
- **Format**: Human-readable plain text with structured sections
- **Ledgers**: `party.ledger`, `locations.ledger`, `npc.ledger`, `world_facts.ledger`, `active_clocks.ledger`, `inventory.ledger`

### Framework & Library Stack

| Category | Library | Version Constraint |
|----------|---------|-------------------|
| Discord Integration | `discord.py` | Latest |
| AI Generation | `google-genai` | Latest |
| Environment Config | `python-dotenv` | Latest |
| PDF Processing | `pymupdf`, `pymupdf4llm[ocr,layout]` | Latest |
| Data Rendering | `prettytable` | Latest |
| Testing | `pytest`, `pytest-asyncio` | Latest |
| Progress Feedback | `tqdm` | Latest |

### Code Style Conventions

#### Function Naming
- **Async functions**: Standard snake_case (e.g., `update_ledgers_logic()`)
- **Helper functions**: Descriptive verb phrases (e.g., `load_full_context()`, `render_table_as_ascii()`)
- **Validation**: `validate_*` prefix (e.g., `validate_config()`)

#### Import Organization
```python
# 1. Standard library
import os, sys, re, io, asyncio, time, pathlib

# 2. Third-party frameworks
import discord
from google import genai
from google.genai import types

# 3. Third-party utilities
from dotenv import load_dotenv
from prettytable import PrettyTable
```

#### Environment Variables
All configuration via `.env` (use `.env.example` as template):
- `DISCORD_TOKEN`, `TARGET_CHANNEL_ID`
- `GEMINI_API_KEY`, `AI_MODEL`, `STORE_ID`
- `PERSONA_FILE`

**Pattern**: Load with `python-dotenv`, validate in `validate_config()`.

---

## 3. Domain Constraints

### Discord-Specific Rules

#### Message Length
- **Narrative Hard Limit**: 1,900 characters (Leave buffer towards the 2,000 characters limit of Discord API)
- **Enforcement**: GM persona instruction + bot.py chunking logic

#### Formatting Restrictions
Discord does not support:
- Standard Markdown tables (use ASCII via `prettytable`)
- Traditional headers `#` (use `**bold text**` instead)
- Indented bullet points (no leading spaces/tabs allowed)

**Solution**: GM persona includes Discord-specific formatting guide.

### RPG Game Master Constraints

#### Fiction-First Philosophy
- **Never railroad**: React to player choices, don't predetermine outcomes
- **Dice are random**: No fudging results
- **Granular pacing**: One plot point at a time, ensure all players get spotlight

#### Social Logic
The AI must detect when to remain silent (`[SIGNAL: SILENCE]`):
- Players roleplaying amongst themselves (no GM input requested)
- Awaiting responses from all party members
- Discussion not addressing NPCs or game mechanics

#### Memory Update Protocol
**MANDATORY** after any state-changing event:
```markdown
| ```MEMORY_UPDATE
| - [Specific fact about what changed]
| - [Another discrete piece of campaign data]
| ```
```

### Visual Generation Constraints

#### Art Style Consistency
- **Styleguide Injection**: Append `.style` files from `knowledge/` to all `VISUAL_PROMPT` requests
- **Safe-Dark Guidelines**: Use artistic euphemisms (e.g., "crimson ichor" not "blood") to avoid safety filters
- **Format**: Always use bracketed structure `[Subject:...] [Setting:...] [Lighting:...] [Style:...]`

#### Image Generation Model
- **Primary**: `gemini-2.5-flash-image` (Nano Banana)
- **Fallback**: Handle safety blocks gracefully with in-fiction error messages

---

## 4. Operational Protocols

### For Future AI Agents

#### Task Management
When working on this repository:

1. **Create/Update `task.md`** in artifacts directory:
   ```markdown
   # Task: [Objective]
   - [ ] Item 1
   - [/] Item 2 (in progress)
   - [x] Item 3 (complete)
   ```

2. **Use Planning Mode** for significant changes:
   - Draft `implementation_plan.md` for user review
   - Wait for approval before executing
   - Update plan if requirements change

3. **Track Progress** via task boundaries:
   - Set `TaskName` for current objective
   - Update `TaskStatus` with next steps (not what was done)
   - Keep `TaskSummary` cumulative

#### Development Workflow

##### Running the Bot
```bash
# Discord mode (live)
python bot.py

# Terminal test mode
python bot.py --terminal
```

##### Testing
```bash
# Run full test suite
./venv/bin/pytest tests/

# Run specific test file
./venv/bin/pytest tests/test_bot_logic.py

# Run with coverage
./venv/bin/pytest tests/ --cov=bot
```

##### Adding Dependencies
1. Add to `requirements.txt`
2. Run `pip install -r requirements.txt`
3. Update this AGENTS.md if it changes architectural patterns

##### Knowledge Base Updates
```bash
# Index new PDFs
python scripts/index_knowledge.py

# High-fidelity ingestion (preserves layout)
python scripts/ingest_rpg_book.py pdf/your_book.pdf
```

#### Artifact Creation for Local Review

When creating walkthroughs or demonstrations for review within the Antigravity IDE:

1. **Capture Workflow**: Use browser_subagent with `RecordingName` for video artifacts.
2. **Generate Screenshots**: Embed in walkthrough.md with `![description](/absolute/path.png)`.
3. **IDE Optimization**: The user reviews code and artifacts directly within the Antigravity IDE.
   - Use carousels for sequentially related images.
   - Embed source code links using the `[text](file:///path/to/file#Lstart-Lend)` format.
   - Ensure markdown formatting is standard and readable in the IDE viewer.

4. **Embedding Syntax**:
   ```markdown
   # Correct
   ![Screenshot of feature](/path/to/image.png)
   
   # Incorrect (won't embed)
   [image.png](/path/to/image.png)
   ```

---

## 5. Development Conventions

### Testing Requirements

#### Test Coverage Expectations
- **Minimum**: all tests passing (current baseline)
- **Categories**:
  - `test_basics.py` - Environment validation
  - `test_bot_logic.py` - Protocol parsing (DATA_TABLE, MEMORY_UPDATE, VISUAL_PROMPT)
  - `test_commands.py` - Discord command handlers (async)
  - `test_integration.py` - Gemini API connectivity
  - `test_memory_system.py` - Ledger persistence

#### AsyncMock for Async Code
```python
from unittest.mock import AsyncMock

# Mocking async Gemini calls
with patch("bot.client_genai.aio.models.generate_content", new_callable=AsyncMock) as mock_gen:
    mock_gen.return_value = mock_response
    await update_ledgers_logic("test fact")
```

#### Test Execution Standards
- All tests must pass before committing
- Use `pytest -v` for verbose output during debugging
- Mock external dependencies (Gemini API, Discord client)

### File Organization

```
game-master/
├── bot.py                  # Main application entry point
├── personas/               # AI personality definitions
│   ├── gm_persona.md
│   ├── memory_architect_persona.md
│   ├── art_analyzer_persona.md
│   └── rpg_scribe_instructions.md
├── memory/                 # Persistent campaign state (.ledger files)
├── knowledge/              # Ingested sourcebooks (.md) and art styles (.style)
├── pdf/                    # Source PDFs for RAG indexing
├── scripts/                # Utility tools
│   ├── index_knowledge.py
│   ├── ingest_rpg_book.py
│   ├── analyze_art_style.py
│   └── check_env.py
└── tests/                  # pytest test suite
```

### Adding New Features

#### Protocol Block Pattern
1. Define format in `gm_persona.md`
2. Add regex parser to `process_response_formatting()`
3. Implement handler in `on_message` event
4. Add unit tests in `test_bot_logic.py`
5. Document in this AGENTS.md

#### New Persona Pattern
1. Create `personas/your_persona.md`
2. Load in relevant script/function via `pathlib.Path().read_text()`
3. Use as `system_instruction` in Gemini config
4. Document persona purpose in this file

---

## 6. Known Issues & Constraints

### Discord Rate Limits
- **Error**: `RESOURCE_EXHAUSTED` from Gemini API during heavy usage
- **Handling**: Automatic retry logic with exponential backoff in `bot.py`
- **Fallback**: Switches to `gemini-1.5-flash-8b` if daily quota exceeded

### Memory System Limitations
- **No Transactions**: Ledger updates are non-atomic (file writes)
- **No Validation**: Ledger content is free-form text (trust AI to format correctly)
- **Manual Reset**: `/reset_memory` requires 2-minute confirmation timeout

### Image Generation Safety
- **Block Rate**: ~10-15% of prompts blocked by safety filters
- **Mitigation**: "Safe-Dark" style guidelines in GM persona
- **Fallback**: In-fiction error message if generation fails

---

## 7. Future Agent Guidance

### Before Making Changes
1. Read this AGENTS.md completely
2. Run existing tests to establish baseline (`pytest tests/`)
3. Check `.env.example` for required configuration
4. Review relevant persona files for behavioral context
5. Suggest updates to this AGENTS.md if patterns need to be updated
6. Update `tasks.md` with any new tasks
7. Show the user the implementation plan
8. Wait for user explicit approval to proceed with implementation

### During Development
1. Use async patterns for all Gemini API calls
2. Add debug logging for new protocol parsers (`print("🔍 ...")`)
3. Update tests concurrently with code changes
4. Keep persona instructions as source of truth for AI behavior

### After Changes
1. Run full test suite (`./venv/bin/pytest tests/`)
2. Test bot in terminal mode (`python bot.py --terminal`)
3. Update this AGENTS.md if additional pattern changes are needed
4. Update README.md if relevant
5. Update `tasks.md` (Local developers only; do not document in `README.md`)
6. Update `roadmap.md` if strategic vision changes
7. Create walkthrough.md artifact for significant features

---

## 8. Glossary

- **GM**: Game Master (the AI bot's primary role)
- **RAG**: Retrieval-Augmented Generation (PDF knowledge lookup)
- **Ledger**: Persistent memory file (.ledger extension)
- **Persona**: AI system instruction defining behavior
- **Protocol Block**: Structured markdown block (e.g., DATA_TABLE, MEMORY_UPDATE)
- **TTRPG**: Tabletop Role-Playing Game
- **Fiction-First**: Narrative-driven gameplay philosophy
- **Nano Banana**: Internal nickname for Gemini 2.5 Flash Image model

---

**This document is the source of truth. When in doubt, defer to patterns established in this file.**
