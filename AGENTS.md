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
- Provide intelligent rule lookups via full-context Markdown ingestion of sourcebooks
- Generate atmospheric artwork using AI image generation
- Maintain persistent campaign memory across bot restarts

### Technology Foundation
- **Language**: Python 3.10+
- **Platform**: Discord (async event-driven architecture)
- **AI Provider**: Google Gemini API
  - `gemini-2.0-flash-lite` for text generation (GM narration)
  - `gemini-2.5-flash-image` for visual generation
- **Knowledge Base**: Context-Full (Direct Markdown ingestion into System Instruction)

---

## 2. Established Patterns

### Architectural Decisions

#### Slash Command Architecture
The bot's primary user interface is built on **native Discord Slash Commands**. This replaces legacy text-based command parsing (`/command`) for all player-facing actions (`/roll`, `/sheet`, `/help`, etc.). This approach provides a better user experience through auto-completion, clear argument structures, and explicit command discovery. The `on_message` handler in `bot.py` is now reserved for processing in-character narrative text and not command logic.

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

#### System Event Injection
A core pattern for slash commands that need to influence the narrative is **System Event Injection**. Instead of the command's code directly performing a complex action, it injects a formatted, high-priority message into the AI's context for the next turn. This allows the AI narrator to process the request with full narrative awareness.

**Example**: `/visual "a mysterious door"` injects `[System Event: Player @PlayerName has requested a visual of "a mysterious door"...]`. The AI then generates the detailed `VISUAL_PROMPT` block itself. This pattern is used for `/visual`, `/rewind`, `/ooc`, and `/x`.

#### Command State Management
For slash commands that require multi-step user interaction (e.g., `/rewind` awaiting a `new_direction`), the bot employs temporary state management. When such a command is initiated, the bot enters an "awaiting input" state for the specific user.

**Behavior**: During this state, other game-related commands from the same user or conflicting commands from other users may be temporarily ignored, or the bot may issue a message prompting completion of the current interaction, to prevent logical conflicts and maintain coherent command processing.

#### Player Identity Mapping
The bot maintains a persistent mapping between Discord User IDs (`<@ID>`) and in-game Character Names. This mapping is critical for commands like `/sheet` to correctly identify which character a player is referring to, whether themselves or another player.

**Mechanism**: A dedicated storage (e.g., `memory/player_map.json` or a specific `.ledger` file) will store these associations. This ensures that character-specific commands operate on the correct in-game entity.

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

| ```DICE_ROLL
| [Character Name] rolls [dice notation] for [reason]
| ```

| ```ROLL_CALL
| @PlayerName: [dice notation] for [reason]
| ```
```

**Implementation**: `process_response_formatting()` in `bot.py` uses case-insensitive regex with fallback patterns.

**DICE_ROLL Protocol**: The AI Game Master uses this block to request dice rolls from the Python dice system instead of simulating results. The bot extracts dice notation (e.g., `2d6+3`, `1d20`), calls `dice.py` to generate true random results, and replaces the block with formatted output before sending to Discord.

**ROLL_CALL Protocol** (Future Enhancement): The AI uses this block to queue a roll request for a specific player. The player can then execute the roll by typing `/roll` without arguments. This creates a smoother gameplay flow where players don't need to manually type dice notation.

**Example Flow**:
```
GM outputs: ```ROLL_CALL
@Alistair: 2d6+3 for Defy Danger
```
Bot displays: 📋 **Alistair**, roll 2d6+3 for Defy Danger
Player types: /roll
Bot executes: 🎲 **Alistair** rolls 2d6+3 for Defy Danger: [4, 5] +3 = **12**
```

#### Persistent Memory System
- **Storage**: File-based `.ledger` files in `memory/` directory
- **Management**: Memory Architect persona processes `MEMORY_UPDATE` blocks
- **Format**: Human-readable plain text with structured sections
- **Ledgers**: `party.ledger`, `locations.ledger`, `npc.ledger`, `world_facts.ledger`, `active_clocks.ledger`, `inventory.ledger`
- **Memory Reversal**: For commands like `/rewind` and `/x` that alter past narrative, explicit instructions are sent to the Memory Architect persona. These instructions either invalidate or counteract previous `MEMORY_UPDATE` facts, ensuring the `.ledger` files accurately reflect the revised game state.

#### Dice Integrity System
- **Module**: `dice.py` - Standalone Python module for true random dice rolls
- **Philosophy**: "Respect the Dice" - All randomness comes from Python's `secrets` module, never from AI
- **Notation Support**: Standard TTRPG dice notation (e.g., `2d6+3`, `1d20`, `4d8-2`, `1d100`)
- **Integration Points**:
  1. **AI Interception**: `DICE_ROLL` protocol blocks in AI responses
  2. **Manual Rolls**: `/roll` Discord command for player-initiated rolls
  3. **Validation**: Malformed dice expressions return user-friendly error messages

**Pattern**: The AI requests rolls via protocol blocks; the bot executes them with cryptographically secure randomness.

### Away Mode System
- **Module**: `away.py` - State manager for player availability
- **Storage**: `memory/away_status.json` (JSON persistence)
- **Philosophy**: "Seamless Absence" - The game continues without friction, and returning players are reintegrated smoothly.
- **Data Schema**:
  ```json
  {
      "user_id": {
          "mode": "str", // "Auto-Pilot", "Off-Screen", "Narrative Exit"
          "last_seen_message_id": "int",
          "timestamp": "float"
      }
  }
  ```
- **Architectural Patterns**:
  1. **Mention Suppression (Dual-Layer)**:
     - **Layer 1 (Prompt)**: Dynamic system instruction explicitly lists users to avoid tagging.
     - **Layer 2 (Filter)**: Output processing regex strips `<@ID>` for away users if the AI hallucinates a tag.
  2. **Just-in-Time Catch-Up**:
     - When a player returns (`/back`), the bot fetches history *after* their `last_seen_message_id`.
     - A targeted "Catch-Up Summary" is generated and sent ephemerally.
  3. **Context Injection**:
     - The "Away Status Block" is injected into the system prompt, defining exactly how the GM should roleplay (or ignore) specific absent characters.

### Dice System Architecture

#### Module: `dice.py`

**Core Function**: `roll(notation: str) -> DiceResult`

**Supported Notation**:
- Basic: `1d20`, `2d6`, `3d8`
- With modifiers: `2d6+3`, `1d20-2`, `4d8+5`
- Percentile: `1d100` or `d%`
- Fudge/FATE: `4dF` (returns -1, 0, or +1 per die)

**Return Structure**:
```python
@dataclass
class DiceResult:
    notation: str          # Original notation (e.g., "2d6+3")
    rolls: List[int]       # Individual die results (e.g., [4, 5])
    modifier: int          # Modifier applied (e.g., 3)
    total: int            # Final sum (e.g., 12)
    formatted: str        # Discord-ready string (e.g., "[4, 5] +3 = **12**")
```

**Error Handling**:
- Invalid notation returns `DiceResult` with `error` field populated
- Validation prevents: negative dice counts, dice > d1000, more than 100 dice per roll
- Graceful degradation: malformed input returns helpful error message

**Integration Pattern**:
```python
# In bot.py
from dice import roll

# Manual player roll
@client_discord.tree.command(name="roll", description="Roll dice (e.g., 2d6+3)")
async def roll_command(interaction, notation: str):
    result = roll(notation)
    await interaction.response.send_message(result.formatted)

# AI roll interception
def process_dice_rolls(text: str) -> str:
    pattern = r'```DICE_ROLL\n(.+?)\n```'
    matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
    for match in matches:
        # Extract notation, call roll(), replace block
        ...
```

**Testing Requirements**:
- Unit tests for notation parsing (valid and invalid)
- Statistical tests for randomness distribution (chi-square test)
- Edge case validation (extreme values, malformed input)

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
- **Dice are random**: All rolls use Python's `secrets` module via `dice.py` - AI never simulates results
- **Granular pacing**: One plot point at a time, ensure all players get spotlight

#### Safety Tools
The architecture includes formal safety tools to ensure player comfort. The primary tool is the `/x` command (X-Card), which allows any player to discreetly pivot the narrative away from uncomfortable content. This command triggers both a narrative shift and a memory reversal to ensure the problematic content is fully retconned from the game state.

#### Social Logic
The AI must detect when to remain silent (`[SIGNAL: SILENCE]`):
- Players roleplaying amongst themselves (no GM input requested)
- Awaiting responses from all party members
- Discussion not addressing NPCs or game mechanics

**OOC Context Management**: Out-of-character (`/ooc`) messages are formatted with an `[OOC]` tag and included in the AI's message history. The `gm_persona.md` explicitly instructs the AI to *not* treat these as in-character actions but to use them to understand player intent, strategy, or meta-discussion without narratively responding to them as if they were in-game events.

#### Memory Update Protocol
**MANDATORY** after any state-changing event:
```markdown
| ```MEMORY_UPDATE
| - [Specific fact about what changed]
| - [Another discrete piece of campaign data]
| ```
```

#### Visual Generation Constraints
- **AI as Creative Director**: Player-initiated `/visual` commands do not directly call the image model. Instead, they trigger the AI (via a system event injected into context) to generate a `VISUAL_PROMPT` block, enriching it with current narrative context and established art style. This ensures stylistic consistency and narrative relevance.
- **Art Style Consistency**: Append `.style` files from `knowledge/` to all `VISUAL_PROMPT` requests.
- **Safe-Dark Guidelines**: Use artistic euphemisms (e.g., "crimson ichor" not "blood") to avoid safety filters.
- **Format**: Always use bracketed structure `[Subject:...] [Setting:...] [Lighting:...] [Style:...]`.
- **Narrative Synchronization**: After an image is generated (or fails), a system event message is injected into the AI's context to inform it about the visual content, ensuring the narrative remains synchronized with the generated imagery.

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

# Test dice system in isolation
python -c "from dice import roll; print(roll('2d6+3'))"
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
# High-fidelity transcription (PDF -> Markdown)
# Bot loads all .md files from knowledge/ automatically on startup
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
  - `test_bot_logic.py` - Protocol parsing (DATA_TABLE, MEMORY_UPDATE, VISUAL_PROMPT, DICE_ROLL, ROLL_CALL)
  - `test_commands.py` - Discord command handlers (async)
  - `test_integration.py` - Gemini API connectivity
  - `test_memory_system.py` - Ledger persistence
  - `test_dice.py` - Dice notation parsing and roll validation

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
- **New Python scripts/modules**: Must include a `_syntax_check()` function (returning `True`) and a corresponding entry in `tests/test_syntax.py` to ensure importability and basic syntax validity.

### File Organization

```
game-master/
├── bot.py                  # Main application entry point
├── dice.py                 # Dice rolling system (cryptographically secure)
├── away.py                 # Player absence management system
├── personas/               # AI personality definitions
│   ├── gm_persona.md
│   ├── memory_architect_persona.md
│   ├── art_analyzer_persona.md
│   └── rpg_scribe_instructions.md
├── memory/                 # Persistent campaign state (.ledger files)
├── knowledge/              # Ingested sourcebooks (.md) and art styles (.style)
├── pdf/                    # Source PDFs for transcription
├── scripts/                # Utility tools
│   ├── index_knowledge.py
│   ├── ingest_rpg_book.py
│   ├── analyze_art_style.py
│   └── check_env.py
└── tests/                  # pytest test suite
```

### Adding New Features

#### Protocol Block Pattern
1. Define format in `gm_persona.md` (e.g., DICE_ROLL or ROLL_CALL for requesting rolls)
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
- **Secure Reset**: The `/reset_memory` function is implemented as an admin-only slash command. This prevents accidental or unauthorized use and requires explicit confirmation through Discord's UI components.

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
5. Update `tasks.md` with any new tasks - first task is always "Suggest updates to `AGENTS.md` if patterns need to be updated in the scope of this specific objective"

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
- **Context-Full**: Direct Markdown ingestion into System Instruction
- **Ledger**: Persistent memory file (.ledger extension)
- **Persona**: AI system instruction defining behavior
- **Protocol Block**: Structured markdown block (e.g., DATA_TABLE, MEMORY_UPDATE, DICE_ROLL, ROLL_CALL)
- **DICE_ROLL**: Protocol block for AI to request true random dice rolls
- **ROLL_CALL**: Protocol block for AI to queue a roll request for a specific player
- **Dice Notation**: Standard TTRPG format (e.g., `2d6+3` = sum) or Pool format (e.g., `5d6p` = list results)
- **Respect the Dice**: Core principle that randomness must be genuine, never simulated
- **TTRPG**: Tabletop Role-Playing Game
- **Fiction-First**: Narrative-driven gameplay philosophy
- **Nano Banana**: Internal nickname for Gemini 2.5 Flash Image model

---

**This document is the source of truth. When in doubt, defer to patterns established in this file.**
