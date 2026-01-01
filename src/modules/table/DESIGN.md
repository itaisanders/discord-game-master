# Table State Machine Design

## Overview
The **Table State Machine** manages the high-level phase of the game session. It determines when the AI acts as a narrator, when it facilitates world-building, and when it remains silent. This prevents "meta-bleed" (narrating OOC chat) and provides structure to the session (Start -> Play -> Pause -> End).

## Data Structures

### TableState (Enum)
```python
class TableState(Enum):
    IDLE = "IDLE"                   # Between sessions. Bot ignores narrative input.
    SESSION_ZERO = "SESSION_ZERO"   # World-building/Char Gen. Bot is active but meta-focused.
    ACTIVE = "ACTIVE"               # Game on. Bot narrates fully.
    PAUSED = "PAUSED"               # Bio-break/Pizza. Bot ignores narrative input.
    DEBRIEF = "DEBRIEF"             # End of session. Bot prompts for feedback.
```

### StateStorage
A simple JSON or text file `memory/table_state.json` tracks the current state to persist across bot restarts.
```json
{
  "state": "IDLE",
  "last_updated": "2024-01-01T12:00:00"
}
```

## Public Interface

### Functions
`src/modules/table/manager.py`

#### `get_state() -> TableState`
Returns the current state.

#### `set_state(new_state: TableState) -> None`
Transitions to a new state and triggers any entry/exit logic (e.g., logging).

#### `is_narrative_active() -> bool`
Returns `True` if state is `ACTIVE` or `SESSION_ZERO`. Used by `main.py` to decide whether to call the LLM.

### Slash Commands
Managed by `src/modules/table/commands.py`.

The system allows fluid transitions between any states to accommodate the dynamic nature of tabletop games.

| Command | Arguments | Logic |
| :--- | :--- | :--- |
| `/session` | `state` (Choice) | Sets the table state directly to the chosen value. |

**Choices:**
- `start` -> Sets `ACTIVE` (Triggers "Session Start" narrative if coming from IDLE).
- `zero` -> Sets `SESSION_ZERO`.
- `pause` -> Sets `PAUSED`.
- `resume` -> Sets `ACTIVE`.
- `end` -> Sets `DEBRIEF`.
- `close` -> Sets `IDLE`.

*Note: While transitions are fluid, the Bot may still emit different context-aware messages based on the change (e.g., switching from IDLE to ACTIVE triggers an intro, but switching from PAUSED to ACTIVE might just say "Welcome back").*

## Integration Plan

### 1. Message Handling (`main.py`)
Modify the `on_message` event loop:
```python
# Pseudo-code
if message.author.bot: return
if message.content.startswith("/"): return # Commands handled by tree

current_state = table_manager.get_state()

if current_state == TableState.IDLE or current_state == TableState.PAUSED:
    return # Ignore chat

if current_state == TableState.ACTIVE:
    # Process as narrative
    process_narrative(message)

if current_state == TableState.SESSION_ZERO:
    # Process as narrative (possibly with different system prompt in future)
    process_narrative(message)
```

### 2. OOC Handling
Regardless of state, messages starting with `((` or `//` should be treated as OOC and ignored by the narrative engine, or handled explicitly if addressed to the bot.

## Future Expansion (Phase 3)
- **Implicit Triggers**: LLM detects "That's a wrap!" and suggests `/session end`.
- **State-Specific Personas**: `SESSION_ZERO` uses a different system prompt than `ACTIVE`.
